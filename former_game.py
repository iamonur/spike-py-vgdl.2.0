gamefile = "maze.txt"
levelfile = "maze_lvl.txt"

import os

immovable_str = "\n        opponent > Immovable color=BLUE"
chaser_str = "\n        opponent > Chaser color=RED"
mover_str = "\n            opponent > color=DARKBLUE"

skeleton_game = """
BasicGame
    SpriteSet
        goalportal > Immovable color=GREEN
        wall > Immovable color=BLACK
        floor > Immovable color=BROWN{immovable}{chaser}
        players > MovingAvatar
            avatar > alternate_keys=True{mover}
    TerminationSet
        SpriteCounter stype=goalportal win=True
        SpriteCounter stype=opponent win=False
    InteractionSet
        opponent goalportal > stepBack
        avatar wall > stepBack
        opponent wall > stepBack
        goalportal avatar > killSprite
        opponent avatar > killSprite
    LevelMapping
        E > opponent floor
        G > goalportal
        A > avatar floor
        . > floor
"""

dummy_maze = """
wwwwwwww
wA.....w
w......w
w.G....w
w......w
w......w
w.....Ew
wwwwwwww
"""

dummy_actions = [1,2,2,2,3,3,3,0,0,0,1,1,1,2,3]

def register_vgdl_env(domain_file, level_file, observer=None, blocksize=None):
    from gym.envs.registration import register, registry
    level_name = '.'.join(os.path.basename(level_file).split('.')[:-1])
    env_name = 'vgdl_{}-v0'.format(level_name)

    register(
        id=env_name,
        entry_point='vgdl.interfaces.gym:VGDLEnv',
        kwargs={
            'game_file': domain_file,
            'level_file': level_file,
            'block_size': blocksize,
            'obs_type': observer or 'features',
        },
        nondeterministic=True
    )

    return env_name

def test2():
    from vgdl.core import Action
    from vgdl.util.humanplay.human import RecordedController
    import vgdl.interfaces.gym
    import gym
    from gym.envs.registration import register, registry

    gamestr = skeleton_game.format(immovable = "", chaser = chaser_str, mover = "")
    f = open("tempgame.txt", 'w')
    f.write(gamestr)
    f.close()

    f = open("tempgame_lvl0.txt", 'w')
    f.write(dummy_maze)
    f.close()

    env_name = register_vgdl_env("tempgame.txt", "tempgame_lvl0.txt", None, 32)
    controller = RecordedController(env_name, dummy_actions)
    controller.play()


if __name__ == "__main__":
    test2()
