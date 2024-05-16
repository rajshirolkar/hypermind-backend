from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse,JSONResponse, StreamingResponse
from pydantic import Field
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

router = APIRouter(tags=["Posts"])

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import os

app = FastAPI()

UPLOAD_DIR = "videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class VideoFormat(str, Enum):
    mp4 = ".mp4"
    fbx = ".fbx"

# @router.post("/{username}/upload", response_model=PostRead, status_code=201,
#              description="Add a video to the database by uploading it and getting the id. The id can be utilized in the get call retrieve it back")
# async def upload_video(
#     request: Request,
#     current_user: Annotated[UserRead, Depends(get_current_user)],
#     db: Annotated[AsyncSession, Depends(async_get_db)],
#     username:str,
#     title: str = Form(...),
#     description: str = Form(...),
#     file: UploadFile = File(...),
# ):
#     # Validate file extension
#     [fileName, fileFormat] = file.filename.split(".")
#     print(fileFormat)
#     if fileFormat not in  ["mp4","fbx"]:
#         raise HTTPException(status_code=400, detail="Invalid file format. Only .mp4 and .fbx are allowed.")
#     db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)

#     # Validate User
#     if db_user is None:
#         raise NotFoundException("User not found")

#     if current_user["id"] != db_user["id"]:
#         raise ForbiddenException()
    
#     #Add Entry to database with file path
#     post_internal_dict = {}
#     post_internal_dict["title"] = title
#     post_internal_dict["text"] = description if description else ""
#     post_internal_dict["media_url"] = UPLOAD_DIR
#     post_internal_dict["created_by_user_id"] = db_user["id"]
#     post_internal = PostCreateInternal(**post_internal_dict)
#     created_post: PostRead = await crud_posts.create(db=db, object=post_internal)
#     # Save the file

    # file_location = os.path.join(UPLOAD_DIR, str(created_post.id)+"."+str(fileFormat))
    # with open(file_location, "wb") as f:
    #     f.write(await file.read())

    # return created_post

@router.get("/{username}/video/{id}", 
            description="Get the video a video by choosing the right format and entering the username. \n The Id is specific to the video that has been posted and returns a dummy video in all other cases")
# @cache(key_prefix="{username}_post_cache", resource_id_name="id")
async def get_video(
    request: Request, 
    # current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    format: VideoFormat,
    username: str , 
    id: int,
    ):
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, username=username, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")
    db_post: PostRead | None = await crud_posts.get(
        db=db, schema_to_select=PostRead, id=id, created_by_user_id=db_user["id"], is_deleted=False
    )
    # if current_user["id"] != db_user["id"]:
    #     raise ForbiddenException()
    if db_post is None:
        file_location = "videos/10.mp4"
    else:
        file_location = os.path.join(db_post['media_url'],str(id)+format)
    if not os.path.isfile(file_location):
        # raise HTTPException(status_code=404, detail="Video not found")
        file_location = "videos/10.mp4"
    # This alternative return gives us download
    # return FileResponse(path=file_location, media_type='application/octet-stream',filename=str(id)+format)
    media_type = "video/" + format[1:]
    filename = str(id)+format
    return FileResponse(
        path=file_location,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": "inline; filename=\"{}\"".format(filename)}
    )
