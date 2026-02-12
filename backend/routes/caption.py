from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from io import BytesIO
from PIL import Image
from functools import lru_cache
from urllib.parse import urlparse

router = APIRouter(prefix="/caption", tags=["caption"])

@lru_cache(maxsize=1)
def get_caption_model():
    """Load BLIP-large captioning model (cached)"""
    from transformers import BlipProcessor, BlipForConditionalGeneration
    
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    
    return processor, model

class CaptionRequest(BaseModel):
    image_url: str

class CaptionResponse(BaseModel):
    caption: str

@router.post("", response_model=CaptionResponse, summary="Generate image caption")
def generate_caption(request: CaptionRequest):
    """Generate a caption for an image"""
    try:
        if request.image_url.startswith('/media/'):
            raise HTTPException(status_code=400, detail="Please provide absolute URL")
        
        response = requests.get(request.image_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert('RGB')
        
        processor, model = get_caption_model()
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_length=50, num_beams=5)
        caption = processor.decode(out[0], skip_special_tokens=True)
        
        return CaptionResponse(caption=caption)
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")


class BatchCaptionRequest(BaseModel):
    frame_ids: List[int]

class FrameCaption(BaseModel):
    frame_id: int
    caption: str
    error: Optional[str] = None

class BatchCaptionResponse(BaseModel):
    captions: List[FrameCaption]

@router.post("/batch", response_model=BatchCaptionResponse, summary="Generate captions for multiple frames")
def generate_batch_captions(request: BatchCaptionRequest):
    """Generate captions for multiple frames by frame_id"""
    from backend.db.postgres import get_conn
    from backend.services.drive import resolve_path, download_bytes
    from psycopg.rows import dict_row
    
    if not request.frame_ids:
        return BatchCaptionResponse(captions=[])
    
    placeholders = ','.join(['%s'] * len(request.frame_ids))
    sql = f"""
    SELECT 
        f.id as frame_id,
        f.media_key,
        d.media_base_uri
    FROM navis.frames f
    JOIN navis.sequences s ON s.id = f.sequence_id
    JOIN navis.datasets d ON d.id = s.dataset_id
    WHERE f.id IN ({placeholders})
    """
    
    with get_conn() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, request.frame_ids)
        frames = cur.fetchall()
    
    frame_map = {row['frame_id']: row for row in frames}
    processor, model = get_caption_model()
    results = []
    
    for frame_id in request.frame_ids:
        frame = frame_map.get(frame_id)
        if not frame:
            results.append(FrameCaption(
                frame_id=frame_id,
                caption="",
                error="Frame not found in database"
            ))
            continue
        
        try:
            parsed_uri = urlparse(frame['media_base_uri'])
            root_id = parsed_uri.netloc
            
            file_id = resolve_path(root_id, frame['media_key'])
            if not file_id:
                raise Exception(f"Could not resolve path: {frame['media_key']}")
            
            img_bytes = download_bytes(file_id)
            image = Image.open(BytesIO(img_bytes)).convert('RGB')
            
            # BLIP-large generation
            inputs = processor(image, return_tensors="pt")
            out = model.generate(**inputs, max_length=50, num_beams=5)
            caption = processor.decode(out[0], skip_special_tokens=True)
            
            results.append(FrameCaption(
                frame_id=frame_id,
                caption=caption,
                error=None
            ))
            
        except Exception as e:
            results.append(FrameCaption(
                frame_id=frame_id,
                caption="",
                error=str(e)
            ))
    
    return BatchCaptionResponse(captions=results)