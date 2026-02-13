import argparse
import copy
import requests
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# ── Global Configuration ─────────────────────────────────────────────
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID", "")
RUNPOD_BASE_URL = os.environ.get("RUNPOD_BASE_URL", f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}")

print("RUNPOD_ENDPOINT_ID:", RUNPOD_ENDPOINT_ID)
HEADERS = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json",
}

# ── RunPod Serverless API Endpoints ─────────────────────────────────
RUNPOD_RUN_URL = f"{RUNPOD_BASE_URL}/run"
RUNPOD_RUNSYNC_URL = f"{RUNPOD_BASE_URL}/runsync"
RUNPOD_STATUS_URL = f"{RUNPOD_BASE_URL}/status"
RUNPOD_CANCEL_URL = f"{RUNPOD_BASE_URL}/cancel"
RUNPOD_HEALTH_URL = f"{RUNPOD_BASE_URL}/health"
RUNPOD_PURGE_QUEUE_URL = f"{RUNPOD_BASE_URL}/purge-queue"

# ── Test Payloads ────────────────────────────────────────────────────
TEST_INPUT_URL = {
    "input": {
        "image": "https://tinifyai.blob.core.windows.net/tinify/uploads/20260212_011026_3f950617.png",
        "denoise_2511": 1.0,
        "denoise_2509": 1.0,
    }
}


CUSTOM_WORKFLOW_PAYLOAD = {
    
  "102": {
    "inputs": {
      "image": "r_0001.png"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "107": {
    "inputs": {
      "strength": 1,
      "model": [
        "108",
        0
      ]
    },
    "class_type": "CFGNorm",
    "_meta": {
      "title": "CFGNorm"
    }
  },
  "108": {
    "inputs": {
      "shift": 3,
      "model": [
        "117",
        0
      ]
    },
    "class_type": "ModelSamplingAuraFlow",
    "_meta": {
      "title": "ModelSamplingAuraFlow"
    }
  },
  "109": {
    "inputs": {
      "samples": [
        "110",
        0
      ],
      "vae": [
        "111",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "110": {
    "inputs": {
      "seed": 87409643182126,
      "steps": 10,
      "cfg": 1,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": [
        "107",
        0
      ],
      "positive": [
        "120",
        0
      ],
      "negative": [
        "122",
        0
      ],
      "latent_image": [
        "118",
        0
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "111": {
    "inputs": {
      "vae_name": "qwen_image_vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "112": {
    "inputs": {
      "clip_name": "qwen/qwen_2.5_vl_7b.safetensors",
      "type": "qwen_image",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "114": {
    "inputs": {
      "images": [
        "109",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "115": {
    "inputs": {
      "unet_name": "Qwen-Image-Edit-2511-FP8_e4m3fn.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "116": {
    "inputs": {
      "lora_name": "高斯泼溅-Sharp.safetensors",
      "strength_model": 1,
      "model": [
        "115",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "LoraLoaderModelOnly"
    }
  },
  "117": {
    "inputs": {
      "lora_name": "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors",
      "strength_model": 1,
      "model": [
        "116",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "LoraLoaderModelOnly"
    }
  },
  "118": {
    "inputs": {
      "pixels": [
        "125",
        0
      ],
      "vae": [
        "111",
        0
      ]
    },
    "class_type": "VAEEncode",
    "_meta": {
      "title": "VAE Encode"
    }
  },
  "119": {
    "inputs": {
      "prompt": "高斯泼溅,参考图2的场景图，修复图1的场景图透视并修复空白区域",
      "clip": [
        "112",
        0
      ],
      "vae": [
        "111",
        0
      ],
      "image1": [
        "125",
        0
      ],
      "image2": [
        "123",
        0
      ]
    },
    "class_type": "TextEncodeQwenImageEditPlus",
    "_meta": {
      "title": "TextEncodeQwenImageEditPlus"
    }
  },
  "120": {
    "inputs": {
      "reference_latents_method": "index_timestep_zero",
      "conditioning": [
        "119",
        0
      ]
    },
    "class_type": "FluxKontextMultiReferenceLatentMethod",
    "_meta": {
      "title": "Edit Model Reference Method"
    }
  },
  "121": {
    "inputs": {
      "prompt": "",
      "clip": [
        "112",
        0
      ],
      "vae": [
        "111",
        0
      ],
      "image1": [
        "125",
        0
      ],
      "image2": [
        "123",
        0
      ]
    },
    "class_type": "TextEncodeQwenImageEditPlus",
    "_meta": {
      "title": "TextEncodeQwenImageEditPlus"
    }
  },
  "122": {
    "inputs": {
      "reference_latents_method": "index_timestep_zero",
      "conditioning": [
        "121",
        0
      ]
    },
    "class_type": "FluxKontextMultiReferenceLatentMethod",
    "_meta": {
      "title": "Edit Model Reference Method"
    }
  },
  "123": {
    "inputs": {
      "upscale_method": "lanczos",
      "megapixels": 1,
      "resolution_steps": 1,
      "image": [
        "102",
        0
      ]
    },
    "class_type": "ImageScaleToTotalPixels",
    "_meta": {
      "title": "Scale Image to Total Pixels"
    }
  },
  "125": {
    "inputs": {
      "upscale_method": "lanczos",
      "megapixels": 1,
      "resolution_steps": 1,
      "image": [
        "152",
        0
      ]
    },
    "class_type": "ImageScaleToTotalPixels",
    "_meta": {
      "title": "Scale Image to Total Pixels"
    }
  },
  "127": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "109",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "143": {
    "inputs": {
      "device": "cuda",
      "checkpoint_path": ""
    },
    "class_type": "LoadSharpModel",
    "_meta": {
      "title": "Load SHARP Model"
    }
  },
  "144": {
    "inputs": {
      "focal_length_mm": 0,
      "output_prefix": "sharp",
      "model": [
        "143",
        0
      ],
      "image": [
        "164",
        0
      ]
    },
    "class_type": "SharpPredict",
    "_meta": {
      "title": "SHARP Predict (Image to PLY)"
    }
  },
  "150": {
    "inputs": {
      "rgthree_comparer": {
        "images": [
          {
            "name": "A",
            "selected": True,
            "url": "/api/view?filename=rgthree.compare._temp_bceym_00001_.png&type=temp&subfolder=&rand=0.9515024019670669"
          },
          {
            "name": "B",
            "selected": True,
            "url": "/api/view?filename=rgthree.compare._temp_bceym_00002_.png&type=temp&subfolder=&rand=0.9052791945165881"
          }
        ]
      },
      "image_a": [
        "109",
        0
      ],
      "image_b": [
        "125",
        0
      ]
    },
    "class_type": "Image Comparer (rgthree)",
    "_meta": {
      "title": "Image Comparer (rgthree)"
    }
  },
  "151": {
    "inputs": {
      "images": [
        "152",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "152": {
    "inputs": {
      "preview_gaussian_v2": "",
      "ply_path": [
        "144",
        0
      ],
      "extrinsics": [
        "144",
        1
      ],
      "intrinsics": [
        "144",
        2
      ]
    },
    "class_type": "GaussianViewer",
    "_meta": {
      "title": "GaussianViewer"
    }
  },
  "153": {
    "inputs": {
      "font_file": "Alibaba-PuHuiTi-Heavy.ttf",
      "font_size": 40,
      "border": 8,
      "color_theme": "light",
      "reel_1": [
        "155",
        0
      ]
    },
    "class_type": "LayerUtility: ImageReelComposit",
    "_meta": {
      "title": "LayerUtility: Image Reel Composit"
    }
  },
  "154": {
    "inputs": {
      "images": [
        "153",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview Image"
    }
  },
  "155": {
    "inputs": {
      "image1_text": "original",
      "image2_text": "2511",
      "image3_text": "2509",
      "image4_text": "lora-20",
      "reel_height": 1024,
      "border": 32,
      "image1": [
        "123",
        0
      ],
      "image2": [
        "109",
        0
      ],
      "image3": [
        "157",
        0
      ]
    },
    "class_type": "LayerUtility: ImageReel",
    "_meta": {
      "title": "LayerUtility: Image Reel"
    }
  },
  "156": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "157",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "157": {
    "inputs": {
      "positive_prompt": "高斯泼溅,参考图2的场景图，修复图1的场景图透视并修复空白区域",
      "negative_prompt": "",
      "generation_mode": "图生图 image-to-image",
      "batch_size": 1,
      "width": [
        "165",
        0
      ],
      "height": [
        "165",
        1
      ],
      "seed": 89039576340055,
      "steps": 8,
      "cfg": 1,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "auraflow_shift": 3,
      "cfg_norm_strength": 1,
      "enable_clean_gpu_memory": False,
      "enable_clean_cpu_memory_after_finish": False,
      "enable_sound_notification": False,
      "auto_save_output_folder": "",
      "output_filename_prefix": "auto_save",
      "instruction": "Describe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.",
      "model": [
        "163",
        0
      ],
      "clip": [
        "161",
        0
      ],
      "vae": [
        "160",
        0
      ],
      "image1": [
        "125",
        0
      ],
      "image2": [
        "123",
        0
      ]
    },
    "class_type": "QwenImageIntegratedKSampler",
    "_meta": {
      "title": "🐋 Qwen Image Integrated KSampler - Github:﹫luguoli"
    }
  },
  "158": {
    "inputs": {
      "lora_name": "Qwen-Image-Lightning-8steps-V1.1.safetensors",
      "strength_model": 1,
      "model": [
        "159",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "LoraLoaderModelOnly"
    }
  },
  "159": {
    "inputs": {
      "unet_name": "qwen_image_edit_2509_fp8_e4m3fn.safetensors",
      "weight_dtype": "default"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "Load Diffusion Model"
    }
  },
  "160": {
    "inputs": {
      "vae_name": "qwen_image_vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "161": {
    "inputs": {
      "clip_name": "qwen/qwen_2.5_vl_7b.safetensors",
      "type": "stable_diffusion",
      "device": "default"
    },
    "class_type": "CLIPLoader",
    "_meta": {
      "title": "Load CLIP"
    }
  },
  "162": {
    "inputs": {
      "rgthree_comparer": {
        "images": [
          {
            "name": "A",
            "selected": True,
            "url": "/api/view?filename=rgthree.compare._temp_lssqi_00001_.png&type=temp&subfolder=&rand=0.6417405152897208"
          },
          {
            "name": "B",
            "selected": True,
            "url": "/api/view?filename=rgthree.compare._temp_lssqi_00002_.png&type=temp&subfolder=&rand=0.12149457913259287"
          }
        ]
      },
      "image_a": [
        "157",
        0
      ],
      "image_b": [
        "125",
        0
      ]
    },
    "class_type": "Image Comparer (rgthree)",
    "_meta": {
      "title": "Image Comparer (rgthree)"
    }
  },
  "163": {
    "inputs": {
      "lora_name": "高斯泼溅-Sharp.safetensors",
      "strength_model": 1,
      "model": [
        "158",
        0
      ]
    },
    "class_type": "LoraLoaderModelOnly",
    "_meta": {
      "title": "LoraLoaderModelOnly"
    }
  },
  "164": {
    "inputs": {
      "upscale_method": "lanczos",
      "megapixels": 1,
      "resolution_steps": 1,
      "image": [
        "102",
        0
      ]
    },
    "class_type": "ImageScaleToTotalPixels",
    "_meta": {
      "title": "Scale Image to Total Pixels"
    }
  },
  "165": {
    "inputs": {
      "image": [
        "102",
        0
      ]
    },
    "class_type": "GetImageSize+",
    "_meta": {
      "title": "🔧 Get Image Size"
    }
  }
}

# ── Workflow Builder ─────────────────────────────────────────────────
def update_workflow_from_input(test_input: dict) -> dict:
    """Update CUSTOM_WORKFLOW_PAYLOAD with values from a test input payload.

    Args:
        test_input: A dict with "input" key containing generation parameters
                    (same format as TEST_INPUT_URL).

    Returns:
        A new workflow dict with the input values applied.
    """
    wf = copy.deepcopy(CUSTOM_WORKFLOW_PAYLOAD)
    inp = test_input.get("input", {})

    # Node 102 - LoadImage
    if "image" in inp:
        wf["102"]["inputs"]["image"] = inp["image"]

    # Node 119 - TextEncodeQwenImageEditPlus (positive prompt for 2511)
    if "prompt" in inp:
        wf["119"]["inputs"]["prompt"] = inp["prompt"]

    # Node 121 - TextEncodeQwenImageEditPlus (negative prompt for 2511)
    if "negative_prompt" in inp:
        wf["121"]["inputs"]["prompt"] = inp["negative_prompt"]

    # Node 110 - KSampler (pipeline 2511)
    if "seed_2511" in inp:
        wf["110"]["inputs"]["seed"] = inp["seed_2511"]
    if "steps_2511" in inp:
        wf["110"]["inputs"]["steps"] = inp["steps_2511"]
    if "denoise_2511" in inp:
        wf["110"]["inputs"]["denoise"] = inp["denoise_2511"]
    if "cfg" in inp:
        wf["110"]["inputs"]["cfg"] = inp["cfg"]

    # Node 108 - ModelSamplingAuraFlow (shift for 2511)
    if "shift" in inp:
        wf["108"]["inputs"]["shift"] = inp["shift"]

    # Node 157 - QwenImageIntegratedKSampler (pipeline 2509)
    if "prompt" in inp:
        wf["157"]["inputs"]["positive_prompt"] = inp["prompt"]
    if "negative_prompt" in inp:
        wf["157"]["inputs"]["negative_prompt"] = inp["negative_prompt"]
    if "seed_2509" in inp:
        wf["157"]["inputs"]["seed"] = inp["seed_2509"]
    if "steps_2509" in inp:
        wf["157"]["inputs"]["steps"] = inp["steps_2509"]
    if "denoise_2509" in inp:
        wf["157"]["inputs"]["denoise"] = inp["denoise_2509"]
    if "cfg" in inp:
        wf["157"]["inputs"]["cfg"] = inp["cfg"]
    if "shift" in inp:
        wf["157"]["inputs"]["auraflow_shift"] = inp["shift"]

    return wf


# ── Helper Functions ─────────────────────────────────────────────────
def run_sync(payload: dict) -> dict:
    """Submit job and wait for result (runsync endpoint)."""
    print(f"POST {RUNPOD_RUNSYNC_URL}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    response = requests.post(RUNPOD_RUNSYNC_URL, headers=HEADERS, json=payload, timeout=600)
    response.raise_for_status()
    result = response.json()

    print(f"\nResponse: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result


def run_async(payload: dict) -> str:
    """Submit job asynchronously (run endpoint). Returns job ID."""
    print(f"POST {RUNPOD_RUN_URL}")

    response = requests.post(RUNPOD_RUN_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()

    job_id = result.get("id")
    print(f"Job submitted: {job_id}")
    print(f"Status: {result.get('status')}")
    return job_id


def poll_status(job_id: str, poll_interval: float = 5.0, timeout: float = 600) -> dict:
    """Poll for job completion."""
    url = f"{RUNPOD_STATUS_URL}/{job_id}"
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            print(f"Timed out after {timeout}s")
            return {"error": "timeout"}

        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        result = response.json()

        status = result.get("status")
        print(f"[{elapsed:.0f}s] Status: {status}")

        if status in ("COMPLETED", "FAILED"):
            print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        time.sleep(poll_interval)


def cancel_job(job_id: str) -> dict:
    """Cancel a running job."""
    url = f"{RUNPOD_CANCEL_URL}/{job_id}"
    response = requests.post(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def check_health() -> dict:
    """Check endpoint health."""
    response = requests.get(RUNPOD_HEALTH_URL, headers=HEADERS, timeout=10)
    response.raise_for_status()
    result = response.json()
    print(f"Health: {json.dumps(result, indent=2)}")
    return result


# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RunPod Endpoint Test Script",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health
    subparsers.add_parser("health", help="Check endpoint health")

    # sync
    subparsers.add_parser("sync", help="Run job synchronously (runsync)")

    # async
    subparsers.add_parser("async", help="Run job asynchronously (run + poll)")

    # status
    sp_status = subparsers.add_parser("status", help="Poll status of a job")
    sp_status.add_argument("job_id", help="Job ID to check")

    # cancel
    sp_cancel = subparsers.add_parser("cancel", help="Cancel a running job")
    sp_cancel.add_argument("job_id", help="Job ID to cancel")

    # custom
    subparsers.add_parser("custom", help="Run custom workflow updated from TEST_INPUT_URL")

    # preview
    subparsers.add_parser("preview", help="Print the updated workflow payload (no API call)")

    args = parser.parse_args()

    print("=" * 60)
    print("RunPod Endpoint Test Script")
    print("=" * 60)

    if args.command == "health":
        check_health()

    elif args.command == "sync":
        print("\n--- Sync Run ---")
        updated_workflow = update_workflow_from_input(TEST_INPUT_URL)
        payload = {"input": {"workflow": updated_workflow}}
        result = run_sync(payload)
        print(f"\nFinal status: {result.get('status')}")
        if result.get("output"):
            print(f"Output: {json.dumps(result['output'], indent=2, ensure_ascii=False)}")

    elif args.command == "async":
        print("\n--- Async Run ---")
        updated_workflow = update_workflow_from_input(TEST_INPUT_URL)
        payload = {"input": {"workflow": updated_workflow}}
        job_id = run_async(payload)
        result = poll_status(job_id)
        print(f"\nFinal status: {result.get('status')}")
        if result.get("output"):
            print(f"Output: {json.dumps(result['output'], indent=2, ensure_ascii=False)}")

    elif args.command == "status":
        print(f"\n--- Polling job {args.job_id} ---")
        result = poll_status(args.job_id)
        print(f"\nFinal status: {result.get('status')}")
        if result.get("output"):
            print(f"Output: {json.dumps(result['output'], indent=2, ensure_ascii=False)}")

    elif args.command == "cancel":
        print(f"\n--- Cancelling job {args.job_id} ---")
        result = cancel_job(args.job_id)
        print(f"Result: {json.dumps(result, indent=2)}")

    elif args.command == "custom":
        print("\n--- Custom Workflow Run ---")
        updated_workflow = update_workflow_from_input(TEST_INPUT_URL)
        custom_payload = {"input": {"workflow": updated_workflow}}
        print(f"Updated nodes: {json.dumps({k: v['inputs'] for k, v in updated_workflow.items() if k in ('102', '108', '110', '119', '121', '157')}, indent=2, ensure_ascii=False)}")
        job_id = run_async(custom_payload)
        result = poll_status(job_id)
        print(f"\nFinal status: {result.get('status')}")
        if result.get("output"):
            print(f"Output: {json.dumps(result['output'], indent=2, ensure_ascii=False)}")

    elif args.command == "preview":
        print("\n--- Updated Workflow Preview ---")
        updated_workflow = update_workflow_from_input(TEST_INPUT_URL)
        payload = {"input": {"workflow": updated_workflow}}
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
