from fastapi import FastAPI, status, Response, HTTPException, Depends, APIRouter
from .. import models, schemas, oauth2
from typing import List, Optional
from sqlalchemy import func

from sqlalchemy.orm import Session
from ..database import get_db


router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

@router.get("/all_posts", response_model=List[schemas.Post])
def get_index_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()

    return posts

@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),
        limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    # posts = db.query(models.Post).all()

    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return posts
    
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post( post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user) ):

    new_post = models.Post(user_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
  
    return new_post

@router.get("/{id}", response_model=schemas.Post)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user) ):
    # cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(id),))
    # post = cursor.fetchone()

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    
    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user) ):

    post_query = db.query(models.Post).filter(models.Post.id == id)

    post = post_query.first()

    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"cannot DELETE post with id: {id}. It does not exist")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform current action")
    
    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user) ):

    post_query = db.query(models.Post).filter(models.Post.id == id)

    post = post_query.first()
    
    if post == None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Post with ID: {id} does not exist")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Not authorized to perform requested action")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()

    updated_post = post_query.first()

    return updated_post


# CREATE TABLE posts (
# id SERIAL PRIMARY KEY,
# title VARCHAR NOT NULL,
# content VARCHAR NOT NULL,
# published BOOLEAN DEFAULT True NOT NULL,
# created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
# );