import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

# ── Configuration ────────────────────────────────────────────────────
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", "8188"))
COMFYUI_URL = f"http://127.0.0.1:{COMFYUI_PORT}"
COMFYUI_PATH = '/workspace/ComfyUI/'
COMFYUI_INPUT_FOLDER = os.environ.get("COMFYUI_INPUT_FOLDER", "input")
COMFYUI_OUTPUT_FOLDER = os.environ.get("COMFYUI_OUTPUT_FOLDER", "output")

#======================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


#======================================================================
class ComfyClient:
    """Synchronous client for the ComfyUI REST API."""

    def __init__(self, server_url: str, timeout: int = 600):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())

    def _url(self, path: str) -> str:
        return f"{self.server_url}/{path.lstrip('/')}"

    def check_connection(self) -> bool:
        try:
            response = requests.get(self._url("/system_stats"), timeout=10)
            response.raise_for_status()
            stats = response.json()
            devices = stats.get("devices", [])
            if devices:
                dev = devices[0]
                vram = dev.get("vram_total", 0) / (1024 ** 3)
                logger.info(
                    "Client connected | GPU: %s | VRAM: %.1f GB",
                    dev.get("name", "unknown"), vram,
                )
            return True
        except Exception as e:
            logger.error("Connect failed: %s", e)
            return False

    def upload_image(self, image_path: str, subfolder: str = "", overwrite: bool = True) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        files = {"image": (path.name, open(path, "rb"), "image/png")}
        data = {"overwrite": str(overwrite).lower()}
        if subfolder:
            data["subfolder"] = subfolder

        response = requests.post(self._url("/upload/image"), files=files, data=data, timeout=self.timeout)
        response.raise_for_status()
        result = response.json()

        filename = result.get("name", path.name)
        logger.info("Uploaded %s -> %s", path.name, filename)
        return filename

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}

        response = requests.post(self._url("/prompt"), json=payload, timeout=self.timeout)
        if response.status_code != 200:
            logger.error("ComfyUI /prompt error %s: %s", response.status_code, response.text)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(f"ComfyUI queue error: {result['error']}")

        prompt_id = result["prompt_id"]
        logger.info("Queued prompt %s", prompt_id)
        return prompt_id

    def get_history(self, prompt_id: str) -> Optional[Dict]:
        response = requests.get(self._url(f"/history/{prompt_id}"), timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return data.get(prompt_id)

    def wait_for_completion(self, prompt_id: str, poll_interval: float = 2.0) -> Dict:
        start = time.time()
        logger.info("Waiting for prompt %s …", prompt_id[:12])

        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                raise TimeoutError(f"Prompt {prompt_id} timed out after {self.timeout}s")

            history = self.get_history(prompt_id)
            if history is not None:
                status = history.get("status", {})
                if status.get("status_str") == "error":
                    msg = json.dumps(status, indent=2, ensure_ascii=False)
                    raise RuntimeError(f"Execution failed:\n{msg}")
                logger.info("Prompt %s completed in %.1fs", prompt_id[:12], elapsed)
                return history

            time.sleep(poll_interval)

    def download_image(self, filename: str, subfolder: str = "", img_type: str = "output") -> bytes:
        """Download image from ComfyUI."""
        params = {"filename": filename, "type": img_type, "subfolder": subfolder}
        response = requests.get(self._url("/view"), params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.content

    def get_output_images(self, history: Dict) -> Dict[str, List[Dict]]:
        """Extract output image info from history."""
        outputs: Dict[str, List[Dict]] = {}
        for node_id, node_out in history.get("outputs", {}).items():
            if "images" in node_out:
                outputs[node_id] = node_out["images"]
        return outputs

#======================================================================

def download_image_from_url(url: str, subfolder: str = "") -> Path:
    """
    Download image from URL and save to ComfyUI input folder.

    Args:
        url: URL of the image to download
        subfolder: Optional subfolder within COMFYUI_INPUT_FOLDER

    Returns:
        Path to the saved image file
    """
    response = requests.get(url)
    response.raise_for_status()

    if subfolder:
        save_dir = Path(COMFYUI_PATH) / COMFYUI_INPUT_FOLDER / subfolder
    else:
        save_dir = Path(COMFYUI_PATH) / COMFYUI_INPUT_FOLDER

    save_dir.mkdir(parents=True, exist_ok=True)

    image_filename = f"downloaded_{uuid.uuid4().hex[:8]}.png"
    image_path = save_dir / image_filename

    with open(image_path, "wb") as f:
        f.write(response.content)

    logger.info("Downloaded image from %s to %s", url, image_path)
    return image_path


#======================================================================

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for RunPod serverless.
    Accepts a complete ComfyUI API-format workflow JSON.
    Scans LoadImage nodes — if the image value is a URL, downloads it,
    uploads to ComfyUI, and replaces the URL with the local filename.

    Expected input format:
    {
        "input": {
            "workflow": { ... full ComfyUI API-format workflow ... }
        }
    }

    LoadImage nodes can have:
      - A local filename: "image": "r_0001.png"  (used as-is)
      - A URL: "image": "https://example.com/image.png"  (auto-downloaded)
    """
    try:
        inp = event.get("input", {})

        # Validate required fields
        workflow = inp.get("workflow")
        if not workflow:
            return {"error": "No workflow provided"}

        # Initialize ComfyUI client
        client = ComfyClient(COMFYUI_URL)
        if not client.check_connection():
            return {"error": "Cannot connect to ComfyUI"}

        # Scan LoadImage nodes — download URLs and upload to ComfyUI
        for node_id, node in workflow.items():
            if node.get("class_type") == "LoadImage":
                image_value = node.get("inputs", {}).get("image", "")
                if image_value.startswith("http"):
                    logger.info("LoadImage node %s has URL: %s", node_id, image_value)
                    image_path = download_image_from_url(image_value)
                    uploaded_name = client.upload_image(str(image_path))
                    node["inputs"]["image"] = uploaded_name
                    logger.info("Replaced URL with uploaded filename: %s", uploaded_name)

        # Queue workflow
        prompt_id = client.queue_prompt(workflow)

        # Wait for completion
        history = client.wait_for_completion(prompt_id)

        # Collect output filenames
        output_images = client.get_output_images(history)
        results = []
        for node_id, images in output_images.items():
            for img_info in images:
                results.append({
                    "node_id": node_id,
                    "filename": img_info["filename"],
                })

        return {
            "status": "success",
            "prompt_id": prompt_id,
            "images": results,
        }

    except Exception as e:
        logger.error("Handler error: %s", e, exc_info=True)
        return {"error": str(e)}


if __name__ == "__main__":
    import runpod

    logger.info("Starting RunPod serverless handler")
    logger.info("ComfyUI endpoint: %s", COMFYUI_URL)
    runpod.serverless.start({"handler": handler})
