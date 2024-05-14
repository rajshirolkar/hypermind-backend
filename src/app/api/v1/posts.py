from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse,JSONResponse
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.utils.cache import cache
from ...crud.crud_posts import crud_posts
from ...crud.crud_users import crud_users
from ...schemas.post import PostCreate, PostCreateInternal, PostRead, PostUpdate
from ...schemas.user import UserRead

from enum import Enum

router = APIRouter(tags=["posts"])

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os

app = FastAPI()

UPLOAD_DIR = "videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class VideoFormat(str, Enum):
    mp4 = ".mp4"
    fbx = ".fbx"

@router.post("/{username}/upload", response_model=PostRead, status_code=201)
async def upload_video(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    username:str,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
):
    # Validate file extension
    [fileName, fileFormat] = file.filename.split(".")
    print(fileFormat)
    if fileFormat not in  ["mp4","fbx"]:
        raise HTTPException(status_code=400, detail="Invalid file format. Only .mp4 and .fbx are allowed.")
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)

    # Validate User
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()
    
    #Add Entry to database with file path
    post_internal_dict = {}
    post_internal_dict["title"] = title
    post_internal_dict["text"] = description
    post_internal_dict["media_url"] = UPLOAD_DIR+'/'
    post_internal_dict["created_by_user_id"] = db_user["id"]
    post_internal = PostCreateInternal(**post_internal_dict)
    created_post: PostRead = await crud_posts.create(db=db, object=post_internal)
    # Save the file

    file_location = os.path.join(UPLOAD_DIR, str(created_post.id)+"."+str(fileFormat))
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return created_post
    # return JSONResponse(content={
    #     "title": title,
    #     "description": description,
    #     "media_url": UPLOAD_DIR+'/'+file.filename,
    #     "created_by_user_id": username,
    # })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




# @router.post("/{username}/post", response_model=PostRead, status_code=201)
# async def write_post(
#     request: Request,
#     username: str,
#     post: PostCreate,
#     current_user: Annotated[UserRead, Depends(get_current_user)],
#     db: Annotated[AsyncSession, Depends(async_get_db)],
# ) -> PostRead:
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if db_user is None:
#         raise NotFoundException("User not found")

#     if current_user["id"] != db_user["id"]:
#         raise ForbiddenException()

#     post_internal_dict = post.model_dump()
#     post_internal_dict["created_by_user_id"] = db_user["id"]

#     post_internal = PostCreateInternal(**post_internal_dict)
#     created_post: PostRead = await crud_posts.create(db=db, object=post_internal)
#     return created_post


# @router.get("/{username}/posts", response_model=PaginatedListResponse[PostRead])
# @cache(
#     key_prefix="{username}_posts:page_{page}:items_per_page:{items_per_page}",
#     resource_id_name="username",
#     expiration=60,
# )
# async def read_posts(
#     request: Request,
#     username: str,
#     db: Annotated[AsyncSession, Depends(async_get_db)],
#     page: int = 1,
#     items_per_page: int = 10,
# ) -> dict:
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if not db_user:
#         raise NotFoundException("User not found")

#     posts_data = await crud_posts.get_multi(
#         db=db,
#         offset=compute_offset(page, items_per_page),
#         limit=items_per_page,
#         schema_to_select=PostRead,
#         created_by_user_id=db_user["id"],
#         is_deleted=False,
#     )

#     response: dict[str, Any] = paginated_response(crud_data=posts_data, page=page, items_per_page=items_per_page)
#     return response

# @router.get("/{username}/video/{id}", response_model=PostRead)
# @cache(key_prefix="{username}_post_cache", resource_id_name="id")
# async def get_video(
#     request: Request, 
#     username: str, 
#     id: int,
#     db: Annotated[AsyncSession, Depends(async_get_db)],
#     format: VideoFormat = Form(...),
#     ):
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if db_user is None:
#         raise NotFoundException("User not found")
#     db_post: PostRead | None = await crud_posts.get(
#         db=db, schema_to_select=PostRead, id=id, created_by_user_id=db_user["id"], is_deleted=False
#     )
#     if db_post is None:
#         raise NotFoundException("Video not found")
#     file_location = os.path.join(UPLOAD_DIR, str(id)+format)
#     print(file_location)
#     if not os.path.isfile(file_location):
#         raise HTTPException(status_code=404, detail="Video not found")
#     return FileResponse(path=file_location, media_type='application/octet-stream')


# @router.patch("/{username}/post/{id}")
# @cache("{username}_post_cache", resource_id_name="id", pattern_to_invalidate_extra=["{username}_posts:*"])
# async def patch_post(
#     request: Request,
#     username: str,
#     id: int,
#     values: PostUpdate,
#     current_user: Annotated[UserRead, Depends(get_current_user)],
#     db: Annotated[AsyncSession, Depends(async_get_db)],
# ) -> dict[str, str]:
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if db_user is None:
#         raise NotFoundException("User not found")

#     if current_user["id"] != db_user["id"]:
#         raise ForbiddenException()

#     db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id, is_deleted=False)
#     if db_post is None:
#         raise NotFoundException("Post not found")

#     await crud_posts.update(db=db, object=values, id=id)
#     return {"message": "Post updated"}


# @router.delete("/{username}/post/{id}")
# @cache("{username}_post_cache", resource_id_name="id", to_invalidate_extra={"{username}_posts": "{username}"})
# async def erase_post(
#     request: Request,
#     username: str,
#     id: int,
#     current_user: Annotated[UserRead, Depends(get_current_user)],
#     db: Annotated[AsyncSession, Depends(async_get_db)],
# ) -> dict[str, str]:
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if db_user is None:
#         raise NotFoundException("User not found")

#     if current_user["id"] != db_user["id"]:
#         raise ForbiddenException()

#     db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id, is_deleted=False)
#     if db_post is None:
#         raise NotFoundException("Post not found")

#     await crud_posts.delete(db=db, id=id)

#     return {"message": "Post deleted"}


# @router.delete("/{username}/db_post/{id}", dependencies=[Depends(get_current_superuser)])
# @cache("{username}_post_cache", resource_id_name="id", to_invalidate_extra={"{username}_posts": "{username}"})
# async def erase_db_post(
#     request: Request, username: str, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
# ) -> dict[str, str]:
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
#     if db_user is None:
#         raise NotFoundException("User not found")

#     db_post = await crud_posts.get(db=db, schema_to_select=PostRead, id=id, is_deleted=False)
#     if db_post is None:
#         raise NotFoundException("Post not found")

#     await crud_posts.db_delete(db=db, id=id)
#     return {"message": "Post deleted from the database"}