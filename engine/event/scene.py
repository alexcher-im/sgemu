from .base import BaseEvent


SceneEvent = BaseEvent.create_meta('SceneEvent', ())
SceneChangeEvent = SceneEvent.create_meta('SceneChangeEvent', ())  # todo remove this event when instancing done and we have multiple scenes and event managers
GameObjectEvent = SceneEvent.create_meta('GameObjectEvent', ('game_object', ))
ComponentEvent = SceneEvent.create_meta('ComponentEvent', ('component', ))
