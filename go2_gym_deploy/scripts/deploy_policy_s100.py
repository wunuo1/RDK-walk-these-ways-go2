import glob
import pickle as pkl
import lcm
import sys
import libmodel_task
import os
import numpy as np
import pathlib
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from go2_gym_deploy.utils.deployment_runner import DeploymentRunner
from go2_gym_deploy.envs.lcm_agent import LCMAgent
from go2_gym_deploy.utils.cheetah_state_estimator import StateEstimator
from go2_gym_deploy.utils.command_profile import *

# lcm多播通信的标准格式
lc = lcm.LCM("udpm://239.255.76.67:7667?ttl=255")

def load_and_run_policy(label, experiment_name, max_vel=1.0, max_yaw_vel=1.0):
    # load agen/t
    # dirs = glob.glob(f"/root/go2/walk-these-ways-go2-main/go2_gym_deploy/scripts/")
    # logdir = sorted(dirs)[0]
    logdir = "../../runs/gait-conditioned-agility/pretrain-go2/train/142238.667503"
# with open(logdir+"/parameters.pkl", 'rb') as file:
    with open(logdir+"/parameters_cpu.pkl", 'rb') as file:
        pkl_cfg = pkl.load(file)
        # print(pkl_cfg.keys())
        cfg = pkl_cfg["Cfg"]
        # print(cfg.keys())

    print('Config successfully loaded!')

    se = StateEstimator(lc)

    control_dt = 0.02
    command_profile = RCControllerProfile(dt=control_dt, state_estimator=se, x_scale=max_vel, y_scale=0.6, yaw_scale=max_yaw_vel)

    hardware_agent = LCMAgent(cfg, se, command_profile)
    se.spin()

    from go2_gym_deploy.envs.history_wrapper import HistoryWrapper
    hardware_agent = HistoryWrapper(hardware_agent)
    print('Agent successfully created!')

    policy = load_policy(logdir)
    print('Policy successfully loaded!')

    # load runner
    root = f"{pathlib.Path(__file__).parent.resolve()}/../../logs/"
    pathlib.Path(root).mkdir(parents=True, exist_ok=True)
    deployment_runner = DeploymentRunner(experiment_name=experiment_name, se=None,
                                         log_root=f"{root}/{experiment_name}")
    deployment_runner.add_control_agent(hardware_agent, "hardware_closed_loop")
    deployment_runner.add_policy(policy)
    deployment_runner.add_command_profile(command_profile)

    if len(sys.argv) >= 2:
        max_steps = int(sys.argv[1])
    else:
        max_steps = 10000000
    print(f'max steps {max_steps}')

    deployment_runner.run(max_steps=max_steps, logging=True)

def load_policy(logdir):
    body_model = libmodel_task.ModelTask()

    adaptation_model = libmodel_task.ModelTask()
    # 初始化模型
    body_model_name = "../../model/body_s100.hbm"
    adaptation_model_name = "../../model/adaptation_module_s100.hbm"

    body_model.ModelInit(body_model_name)
    adaptation_model.ModelInit(adaptation_model_name)

    def policy(obs, info):
        loaded_data = obs["obs_history"].numpy()
        loaded_data = loaded_data.reshape(1, 1, 2100)
        loaded_data_list = [loaded_data]
        adaptation_model_result = adaptation_model.ModelInfer(loaded_data_list)
        adaptation_model_result = np.array(adaptation_model_result)
        
        adaptation_model_result = adaptation_model_result.reshape(1, 1, 2)

        body_input = np.concatenate((loaded_data, adaptation_model_result), axis=-1)

        body_input_list = [body_input]
        action = body_model.ModelInfer(body_input_list)
        action = np.array(action)
        action = action.reshape(1, 12)

        return torch.from_numpy(action)

    return policy


if __name__ == '__main__':
    # label = "gait-conditioned-agility/pretrain-v0/train"
    label = "gait-conditioned-agility/pretrain-go2/train"

    experiment_name = "example_experiment"

    # default:
    # max_vel=3.5, max_yaw_vel=5.0
    load_and_run_policy(label, experiment_name=experiment_name, max_vel=2.5, max_yaw_vel=5.0)
