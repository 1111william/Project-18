from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_progress():
    return {
        "message": "Progress API initialized"
    }


@router.get("/{child_id}")
def get_child_progress(child_id: int):
    return {
        "child_id": child_id,
        "level": 1,
        "completed_lessons": 3,
        "total_lessons": 5,
        "progress_percent": 60
    }