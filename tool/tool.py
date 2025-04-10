import torch
import os
import copy
import argparse


parser = argparse.ArgumentParser(description="Process weights file")
parser.add_argument("weights_path", type=str, help="Path to the weights file")
parser.add_argument("opset_version", type=int, default=16, help="ONNX opset version (default: 16)")
args = parser.parse_args()
print(f"Processing file: {args.weights_path}")

# weights_path = "../runs/gait-conditioned-agility/2025-03-05/train/084413.014863/checkpoints/ac_weights_024400.pt"
weights_path = args.weights_path
opset_version = args.opset_version
output_path = "model"
os.makedirs(output_path, exist_ok=True)

from go2_gym_learn.ppo_cse.actor_critic import ActorCritic

device = torch.device("cpu")
actor_critic = ActorCritic(70, 2, 2100, 12)
actor_critic.load_state_dict(torch.load(weights_path, map_location=device))
actor_critic.to(device)
actor_critic.eval()

adaptation_module = copy.deepcopy(actor_critic.adaptation_module).to(device)
traced_script_adaptation_module = torch.jit.script(adaptation_module)
adaptation_module_path = f"{output_path}/adaptation_module_latest.jit"
traced_script_adaptation_module.save(adaptation_module_path)

body_model = copy.deepcopy(actor_critic.actor_body).to(device)
traced_script_body_module = torch.jit.script(body_model)
body_path = f"{output_path}/body_latest.jit"
traced_script_body_module.save(body_path)


onnx_adaptation_path = f"{output_path}/adaptation_module_latest.onnx"
onnx_body_path = f"{output_path}/body_latest.onnx"

torch.onnx.export(traced_script_adaptation_module, torch.randn(1, 2100), onnx_adaptation_path,
                  input_names=["obs_history"], output_names=["latent"], opset_version=opset_version)
print(f"Saved adaptation_module to {onnx_adaptation_path} in ONNX format")

torch.onnx.export(traced_script_body_module, torch.randn(1, 2102), onnx_body_path,
                  input_names=["obs_and_latent"], output_names=["action"], opset_version=opset_version)
print(f"Saved body_model to {onnx_body_path} in ONNX format")


print(f"Saved adaptation_module to {adaptation_module_path}")
print(f"Saved body_model to {body_path}")
