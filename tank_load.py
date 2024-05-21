from stable_baselines3 import PPO
from tankenv import TankEnv

models_dir = "models/1715970412"

env = TankEnv(True)
env.reset()

model_path = f"{models_dir}/1200000.zip"
model = PPO.load(model_path, env=env)

episodes = 500

for ep in range(episodes):
    vec_env = model.get_env()
    obs = vec_env.reset()
    done = False
    while not done:
        action, _states = model.predict(obs)
        obs, rewards, done, truncated, info = env.step(action)
        print(rewards)
