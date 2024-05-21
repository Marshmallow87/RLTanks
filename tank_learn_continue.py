from stable_baselines3 import PPO
from tankenv import TankEnv
import time

models_dir = "models/1715365876"
logdir = f"logs/{int(time.time())}/"  # tensorboard --logdir ./PPO_0

env = TankEnv(False)
model_path = f"{models_dir}/4730000.zip"
model = PPO.load(model_path, env=env)
model.set_env(env)

TIMESTEPS = 10000
iters = 0
while True:
    iters += 1
    model.learn(
        total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=f"PPO"
    )
    model.save(f"{models_dir}/{TIMESTEPS*iters}")
