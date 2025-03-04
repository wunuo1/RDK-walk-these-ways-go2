import glob
import pickle as pkl
import lcm
import sys
import libmodel_task
from go2_gym_deploy.utils.deployment_runner import DeploymentRunner
from go2_gym_deploy.envs.lcm_agent import LCMAgent
from go2_gym_deploy.utils.cheetah_state_estimator import StateEstimator
from go2_gym_deploy.utils.command_profile import *
import numpy as np
import pathlib
import onnxruntime as ort

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

    session_adaptation = ort.InferenceSession("../../model/adaptation_module_x511.onnx", providers=["CPUExecutionProvider"])
    session_body = ort.InferenceSession("../../model/body_x511.onnx", providers=["CPUExecutionProvider"])

    input_name_adaptation = session_adaptation.get_inputs()[0].name
    input_name_body = session_body.get_inputs()[0].name

    def policy(obs, info):
        i = 0
        loaded_data = obs["obs_history"].numpy()

        outputs_adaptation = session_adaptation.run(None, {input_name_adaptation: loaded_data})
        outputs_adaptation = np.array(outputs_adaptation, dtype=np.float32)
        print(outputs_adaptation.reshape(1, 2))
        body_input = np.concatenate((loaded_data, outputs_adaptation.reshape(1, 2)), axis=-1)

        outputs_body = session_body.run(None, {input_name_body: body_input})
        outputs_body = np.array(outputs_body, dtype=np.float32)
        outputs_body = outputs_body.reshape(1, 12)
        # print(action)
        return torch.from_numpy(outputs_body)

    return policy


if __name__ == '__main__':
    # label = "gait-conditioned-agility/pretrain-v0/train"
    label = "gait-conditioned-agility/pretrain-go2/train"

    experiment_name = "example_experiment"

    # default:
    # max_vel=3.5, max_yaw_vel=5.0
    load_and_run_policy(label, experiment_name=experiment_name, max_vel=2.5, max_yaw_vel=5.0)
