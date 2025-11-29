"""
Роутер для работы с сессиями чата

Сессия - это диалог с пользователем, в котором собирается информация
о финансовом специалисте через интервью.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response

from app.db.mongo import get_db
from app.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    GetSessionResponse,
    ListSessionsResponse,
    SessionListItem,
    Message,
    Session,
    SessionState,
)
from app.repos.chat_repos import SessionsRepository, MessagesRepository


router = APIRouter()


async def get_sessions_repo(db=Depends(get_db)) -> SessionsRepository:  # noqa: ANN001
    """Получить репозиторий сессий"""
    return SessionsRepository(db)


async def get_messages_repo(db=Depends(get_db)) -> MessagesRepository:  # noqa: ANN001
    """Получить репозиторий сообщений"""
    return MessagesRepository(db)


@router.post("", response_model=CreateSessionResponse)
async def create_session(
    payload: CreateSessionRequest | None = None,
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
) -> CreateSessionResponse:
    """
    Создать новую сессию чата
    
    Args:
        payload: Запрос с опциональным user_id
        sessions_repo: Репозиторий сессий
        
    Returns:
        CreateSessionResponse с ID созданной сессии
    """
    now = datetime.utcnow().isoformat()
    
    # Генерируем user_id, если не указан
    user_id = payload.user_id if payload and payload.user_id else str(uuid4())
    
    # Создаем новую сессию
    session = Session(
        session_id=str(uuid4()),
        user_id=user_id,
        state=SessionState(
            last_question_type=None,
            last_updated_at=now,
        ),
    )
    
    # Сохраняем в базу данных
    await sessions_repo.insert_one(session.model_dump())
    
    return CreateSessionResponse(session_id=session.session_id)


@router.get("/{session_id}", response_model=GetSessionResponse)
async def get_session(
    session_id: str,
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
) -> GetSessionResponse:
    """
    Получить сессию с историей сообщений
    
    Args:
        session_id: ID сессии
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        
    Returns:
        GetSessionResponse с сессией и сообщениями
        
    Raises:
        HTTPException: Если сессия не найдена
    """
    # Получаем сессию
    session_doc = await sessions_repo.find_by_id(session_id)
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Получаем сообщения
    messages_docs = await messages_repo.list_by_session(session_id, limit=50)
    
    # Преобразуем в модели
    session = Session.model_validate(session_doc)
    messages = [Message.model_validate(md) for md in messages_docs]
    
    return GetSessionResponse(session=session, messages=messages)


@router.get("", response_model=ListSessionsResponse)
async def list_sessions(
    user_id: str,
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
) -> ListSessionsResponse:
    """
    Получить список всех сессий пользователя
    
    Args:
        user_id: ID пользователя
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        
    Returns:
        ListSessionsResponse со списком сессий
    """
    # Получаем все сессии пользователя
    sessions_docs = await sessions_repo.list_by_user_id(user_id)
    
    # Для каждой сессии получаем превью последнего сообщения
    sessions_list = []
    for session_doc in sessions_docs:
        session = Session.model_validate(session_doc)
        
        # Получаем последнее сообщение для превью
        last_messages = await messages_repo.list_by_session(session.session_id, limit=1)
        preview = None
        if last_messages:
            last_msg = last_messages[-1]
            preview_text = last_msg.get("content", "")
            if preview_text:
                preview = preview_text[:100] + "..." if len(preview_text) > 100 else preview_text
        
        sessions_list.append(SessionListItem(
            session_id=session.session_id,
            user_id=session.user_id,
            last_updated_at=session.state.last_updated_at,
            preview=preview
        ))
    
    return ListSessionsResponse(sessions=sessions_list)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
) -> dict:
    """
    Удалить сессию и все её сообщения
    
    Args:
        session_id: ID сессии для удаления
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        
    Returns:
        Словарь с результатом удаления
        
    Raises:
        HTTPException: Если сессия не найдена
    """
    # Проверяем существование сессии
    session = await sessions_repo.find_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Удаляем все сообщения сессии
    await messages_repo.delete_by_session_id(session_id)
    
    # Удаляем саму сессию
    await sessions_repo.delete_by_id(session_id)
    
    return {"status": "success", "message": "Session deleted successfully"}


@router.get("/{session_id}/export")
async def export_session_history(
    session_id: str,
    format: str = "pdf",  # pdf или docx
    sessions_repo: SessionsRepository = Depends(get_sessions_repo),
    messages_repo: MessagesRepository = Depends(get_messages_repo),
) -> Response:
    """
    Экспортировать историю сессии в Word или PDF
    
    Args:
        session_id: ID сессии
        format: Формат экспорта (pdf или docx)
        sessions_repo: Репозиторий сессий
        messages_repo: Репозиторий сообщений
        
    Returns:
        Файл с историей чата
        
    Raises:
        HTTPException: Если сессия не найдена
    """
    # Проверяем, что сессия существует
    session_doc = await sessions_repo.find_by_id(session_id)
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Получаем все сообщения
    messages_docs = await messages_repo.get_all_by_session(session_id)
    messages = [Message.model_validate(md) for md in messages_docs]
    
    # Формируем текст истории
    history_text = f"История чата - Сессия {session_id}\n"
    history_text += "=" * 50 + "\n\n"
    
    for msg in messages:
        role_name = "Пользователь" if msg.role.value == "user" else "AI Консультант"
        history_text += f"[{role_name}]:\n{msg.content}\n\n"
        history_text += "-" * 50 + "\n\n"
    
    # Экспортируем в нужном формате
    if format == "docx":
        try:
            from docx import Document
            from docx.shared import Pt
            from io import BytesIO
            
            doc = Document()
            doc.add_heading(f'История чата - Сессия {session_id}', 0)
            
            for msg in messages:
                role_name = "Пользователь" if msg.role.value == "user" else "AI Консультант"
                doc.add_heading(role_name, level=1)
                doc.add_paragraph(msg.content)
                doc.add_paragraph("─" * 50)
            
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            return Response(
                content=buffer.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="chat_history_{session_id}.docx"'}
            )
        except ImportError:
            # Фолбэк на txt, если нет python-docx
            txt = "\n".join(
                (f"{'Пользователь' if m.role.value=='user' else 'AI Консультант'}:\n{m.content}\n" + ("─" * 50))
                for m in messages
            )
            return Response(
                content=txt.encode("utf-8"),
                media_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="chat_history_{session_id}.txt"'}
            )
    
    elif format == "pdf":
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Заголовок
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor='#1e3c72',
                spaceAfter=30,
            )
            story.append(Paragraph(f'История чата - Сессия {session_id}', title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Сообщения
            for msg in messages:
                role_name = "Пользователь" if msg.role.value == "user" else "AI Консультант"
                role_style = ParagraphStyle(
                    'RoleStyle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor='#2a5298',
                    spaceAfter=10,
                )
                story.append(Paragraph(role_name, role_style))
                story.append(Paragraph(msg.content.replace('\n', '<br/>'), styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("─" * 50, styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            doc.build(story)
            buffer.seek(0)
            
            return Response(
                content=buffer.getvalue(),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="chat_history_{session_id}.pdf"'}
            )
        except ImportError:
            # Если нет reportlab, пробуем docx как фолбэк
            try:
                from docx import Document
                from io import BytesIO
                doc = Document()
                doc.add_heading(f'История чата - Сессия {session_id}', 0)
                for msg in messages:
                    role_name = "Пользователь" if msg.role.value == "user" else "AI Консультант"
                    doc.add_heading(role_name, level=1)
                    doc.add_paragraph(msg.content)
                    doc.add_paragraph("─" * 50)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                return Response(
                    content=buffer.getvalue(),
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": f'attachment; filename="chat_history_{session_id}.docx"'}
                )
            except Exception:
                # Последний фолбэк — txt
                txt = "\n".join(
                    (f"{'Пользователь' if m.role.value=='user' else 'AI Консультант'}:\n{m.content}\n" + ('─' * 50))
                    for m in messages
                )
                return Response(
                    content=txt.encode("utf-8"),
                    media_type="text/plain; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="chat_history_{session_id}.txt"'}
                )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'pdf' or 'docx'")

