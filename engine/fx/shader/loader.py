from ...lib.parser import LineFeeder, startswith_poll
from ...lib.pathlib import get_rel_path, join

# bless for glsl optimizer


# [WARNING]: tessellation and geometry shaders are not supported
class Effect:
    @classmethod
    def from_file(cls, module_name, relative=False):
        if relative:
            module_name = get_rel_path(__file__, module_name)
        v_file = join(module_name, 'vert.glsl')
        f_file = join(module_name, 'frag.glsl')
        try:
            v_file = open(v_file).read()
        except FileNotFoundError:
            v_file = ''
        try:
            f_file = open(f_file).read()
        except FileNotFoundError:
            f_file = ''
        return cls(v_file, f_file)

    def __init__(self, vert, frag):
        self.vert = EffectPart(vert)
        self.frag = EffectPart(frag)

    def insert(self, effect, section=0):
        self.vert.insert(effect.vert, section)
        self.frag.insert(effect.frag, section)
        return self

    def head_text(self):
        return self.vert


class EffectPart:
    def __init__(self, text):
        self.text = text
        self.head = ParsedGroup()
        self.main = ParsedGroup()
        self._parse()

    def _parse(self):
        startswith_poll(LineFeeder(self.text.split('\n')),
                        {'//head': on_part, '//main': on_part},
                        self.on_result)

    def on_result(self, phrase, data):
        if phrase == '//head':
            self.head = data
        elif phrase == '//main':
            self.main = data
        # print(phrase)
        # print(data.text())
        # print()

    def insert(self, eff_part, section):
        self.main.insert(eff_part.main(), section)
        self.head.insert(eff_part.head(), section)


def on_part(iterator, line):
    text = ParsedGroup()
    pad = line.split('/')[0]
    pad_len = len(pad)

    def on_section(parts, curr_line):
        parts.back()
        value = int(parts.pop().split('//section')[1])
        text.add_section(value, curr_line.split('/')[0][pad_len:])
    def on_line(line):
        text.add_line(line[pad_len:]) if not line.strip().startswith('//end') else None

    startswith_poll(iterator, {'//section': on_section}, all_poll=on_line, stop='//end')
    return text


class ParsedGroup:  # head or main
    def __init__(self):
        self.lines = [[]]  # list - code, tuple - section

    def add_section(self, section, pad):
        self.lines.append((section, pad))
        self.lines.append([])

    def add_line(self, line):
        self.lines[-1].append(line)

    def insert(self, code, section):
        for i, item in enumerate(self.lines):
            if item and item[0] == section and code:
                pad = item[1]
                form_code = '\n'.join((pad + line for line in code.split('\n')))
                self.lines[i - 1].append(form_code + '\n\n')

    def text(self):
        return '\n'.join(('\n'.join(line) for line in self.lines if isinstance(line, list)))

    def __call__(self):
        return self.text()


class EffectGroup:
    class FakePart:
        def __init__(self, parts):
            self.parts = parts

        @property
        def head(self):
            return lambda: '\n'.join((part.head.text() for part in self.parts))

        @property
        def main(self):
            return lambda: '\n'.join((part.main.text() for part in self.parts))

    def __init__(self, *effects):
        self.effects = effects

    @property
    def vert(self):
        return self.FakePart((effect.vert for effect in self.effects))

    @property
    def frag(self):
        return self.FakePart((effect.frag for effect in self.effects))


class Builder:
    def __init__(self, effect: Effect, defines=()):
        self.effect = effect
        self.defines = ''
        for item in defines:
            if isinstance(item, tuple) or isinstance(item, list):
                defines += '#define %s %s\n' % item
            else:
                defines += '#define %s\n' % item

    @property
    def vert_str(self):
        return self.defines + self.effect.vert.head.text() + '\n' + self.effect.vert.main.text()

    @property
    def frag_str(self):
        return self.defines + self.effect.frag.head.text() + '\n' + self.effect.frag.main.text()
