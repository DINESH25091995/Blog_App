from fastapi import APIRouter, Form, Depends,Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import Comment
from database import get_db
from routers.auth import get_current_user

router = APIRouter()

@router.post("/{blog_id}")
def add_comment(request: Request,blog_id: int, content: str = Form(...), db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect to login page
    comment = Comment(blog_id=blog_id, content=content)
    db.add(comment)
    db.commit()
    return RedirectResponse(url=f"/blogs/{blog_id}", status_code=303)
