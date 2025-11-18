"""
Generic CRUD operations base class.

This module provides a type-safe, async base class for common database
operations (Create, Read, Update, Delete) that can be extended for any
SQLModel entity. It includes pagination, filtering, multi-tenant support,
and advanced query capabilities.

Example:
    ```python
    from src.models import User, UserCreate, UserUpdate
    
    class UserCRUD(CRUDBase[User, UserCreate, UserUpdate]):
        async def get_by_email(
            self, session: AsyncSession, *, email: str
        ) -> Optional[User]:
            return await self.get_by_field(
                session, field="email", value=email
            )
    
    user_crud = UserCRUD(User)
    
    # Create a user
    new_user = await user_crud.create(session, obj_in=user_data)
    
    # Get paginated users with filtering
    users = await user_crud.get_multi(
        session,
        skip=0,
        limit=10,
        filters={"is_active": True},
        order_by="-created_at"
    )
    ```
"""
from __future__ import annotations

import logging
from typing import Any, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

# Type variables for generic CRUD operations
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD operations base class.
    
    This class provides standard database operations that can be inherited
    by specific model CRUD classes. It uses SQLModel for ORM operations
    and supports async/await patterns throughout.
    
    Attributes:
        model: The SQLModel class this CRUD instance operates on.
    
    Type Parameters:
        ModelType: The SQLModel database model type.
        CreateSchemaType: The Pydantic schema for creating instances.
        UpdateSchemaType: The Pydantic schema for updating instances.
    """
    
    def __init__(self, model: Type[ModelType]) -> None:
        """
        Initialize CRUD instance with a model class.
        
        Args:
            model: The SQLModel class to perform operations on.
        """
        self.model = model
    
    async def get(
        self,
        session: AsyncSession,
        id: Any,
        *,
        tenant_id: Optional[str] = None,
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            session: Database session.
            id: Primary key value.
            tenant_id: Optional tenant ID for multi-tenant filtering.
        
        Returns:
            The model instance if found, None otherwise.
        """
        query = select(self.model).where(self.model.id == id)
        
        # Apply tenant filter if multi-tenant is enabled
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
        order_by: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            session: Database session.
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            tenant_id: Optional tenant ID for multi-tenant filtering.
            order_by: Column name to order by (prefix with '-' for DESC).
            filters: Dictionary of field names to values for filtering.
        
        Returns:
            List of model instances matching the criteria.
        
        Example:
            ```python
            # Get active admin users, ordered by creation date
            users = await user_crud.get_multi(
                session,
                skip=10,
                limit=20,
                filters={"is_active": True, "role": "admin"},
                order_by="-created_at"  # Descending order
            )
            ```
        """
        query = select(self.model)
        
        # Apply tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        # Apply custom filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        # Handle IN clause for lists
                        filter_clauses.append(
                            getattr(self.model, field).in_(value)
                        )
                    elif value is None:
                        # Handle NULL checks
                        filter_clauses.append(
                            getattr(self.model, field).is_(None)
                        )
                    else:
                        # Regular equality
                        filter_clauses.append(
                            getattr(self.model, field) == value
                        )
            
            if filter_clauses:
                query = query.where(and_(*filter_clauses))
        
        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                # Descending order
                field_name = order_by[1:]
                if hasattr(self.model, field_name):
                    query = query.order_by(
                        getattr(self.model, field_name).desc()
                    )
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def create(
        self,
        session: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        tenant_id: Optional[str] = None,
        commit: bool = True,
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            session: Database session.
            obj_in: Pydantic schema with creation data.
            tenant_id: Optional tenant ID for multi-tenant records.
            commit: Whether to commit the transaction immediately.
        
        Returns:
            The created model instance.
        
        Raises:
            IntegrityError: If database constraints are violated.
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Add tenant_id if multi-tenant
        if tenant_id and hasattr(self.model, "tenant_id"):
            obj_data["tenant_id"] = tenant_id
        
        db_obj = self.model(**obj_data)
        session.add(db_obj)
        
        if commit:
            try:
                await session.commit()
                await session.refresh(db_obj)
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error creating {self.model.__name__}: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create {self.model.__name__}: {e}")
                raise
        
        return db_obj
    
    async def update(
        self,
        session: AsyncSession,
        *,
        id: Any,
        obj_in: Union[UpdateSchemaType, dict[str, Any]],
        tenant_id: Optional[str] = None,
        commit: bool = True,
    ) -> Optional[ModelType]:
        """
        Update an existing record by ID.
        
        Args:
            session: Database session.
            id: Primary key value.
            obj_in: Update data as Pydantic schema or dictionary.
            tenant_id: Optional tenant ID for multi-tenant safety.
            commit: Whether to commit the transaction immediately.
        
        Returns:
            The updated model instance if found, None otherwise.
        
        Raises:
            IntegrityError: If database constraints are violated.
        """
        # Get existing object
        db_obj = await self.get(session, id, tenant_id=tenant_id)
        if not db_obj:
            return None
        
        # Extract update data
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        
        # Update only provided fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        session.add(db_obj)
        
        if commit:
            try:
                await session.commit()
                await session.refresh(db_obj)
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Integrity error updating {self.model.__name__}: {e}")
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update {self.model.__name__}: {e}")
                raise
        
        return db_obj
    
    async def delete(
        self,
        session: AsyncSession,
        *,
        id: Any,
        tenant_id: Optional[str] = None,
        commit: bool = True,
    ) -> bool:
        """
        Delete a record by ID.
        
        Args:
            session: Database session.
            id: Primary key value.
            tenant_id: Optional tenant ID for multi-tenant safety.
            commit: Whether to commit the transaction immediately.
        
        Returns:
            True if deleted, False if not found.
        """
        db_obj = await self.get(session, id, tenant_id=tenant_id)
        
        if not db_obj:
            return False
        
        await session.delete(db_obj)
        
        if commit:
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete {self.model.__name__}: {e}")
                raise
        
        return True
    
    async def count(
        self,
        session: AsyncSession,
        *,
        tenant_id: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        Count total records matching criteria.
        
        Args:
            session: Database session.
            tenant_id: Optional tenant ID for multi-tenant filtering.
            filters: Dictionary of field names to values for filtering.
        
        Returns:
            Total count of matching records.
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        # Apply custom filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    if isinstance(value, list):
                        filter_clauses.append(
                            getattr(self.model, field).in_(value)
                        )
                    elif value is None:
                        filter_clauses.append(
                            getattr(self.model, field).is_(None)
                        )
                    else:
                        filter_clauses.append(
                            getattr(self.model, field) == value
                        )
            
            if filter_clauses:
                query = query.where(and_(*filter_clauses))
        
        result = await session.execute(query)
        return result.scalar() or 0
    
    async def exists(
        self,
        session: AsyncSession,
        *,
        id: Optional[Any] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Check if record exists.
        
        Args:
            session: Database session.
            id: Primary key value (if checking by ID).
            field: Field name to check (if not using ID).
            value: Value to match (if not using ID).
            tenant_id: Optional tenant ID for multi-tenant filtering.
        
        Returns:
            True if record exists, False otherwise.
        
        Example:
            ```python
            # Check by ID
            exists = await user_crud.exists(session, id=123)
            
            # Check by field
            exists = await user_crud.exists(
                session, field="email", value="user@example.com"
            )
            ```
        """
        query = select(func.count()).select_from(self.model)
        
        if id is not None:
            query = query.where(self.model.id == id)
        elif field and value is not None:
            if not hasattr(self.model, field):
                raise AttributeError(
                    f"Model {self.model.__name__} has no field '{field}'"
                )
            query = query.where(getattr(self.model, field) == value)
        else:
            raise ValueError(
                "Either 'id' or both 'field' and 'value' must be provided"
            )
        
        # Apply tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await session.execute(query)
        count = result.scalar() or 0
        return count > 0
    
    async def get_by_field(
        self,
        session: AsyncSession,
        *,
        field: str,
        value: Any,
        tenant_id: Optional[str] = None,
    ) -> Optional[ModelType]:
        """
        Get a single record by any field.
        
        Args:
            session: Database session.
            field: Field name to filter by.
            value: Value to match.
            tenant_id: Optional tenant ID for multi-tenant filtering.
        
        Returns:
            The first matching model instance if found, None otherwise.
        
        Raises:
            AttributeError: If the field doesn't exist on the model.
        """
        if not hasattr(self.model, field):
            raise AttributeError(
                f"Model {self.model.__name__} has no field '{field}'"
            )
        
        query = select(self.model).where(getattr(self.model, field) == value)
        
        # Apply tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_or_create(
        self,
        session: AsyncSession,
        *,
        defaults: Optional[dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ) -> tuple[ModelType, bool]:
        """
        Get existing record or create new one.
        
        Args:
            session: Database session.
            defaults: Default values to use when creating.
            tenant_id: Optional tenant ID for multi-tenant records.
            **kwargs: Field values to search by and use for creation.
        
        Returns:
            Tuple of (instance, created) where created is True if
            a new record was created.
        
        Example:
            ```python
            user, created = await user_crud.get_or_create(
                session,
                email="user@example.com",
                defaults={"name": "New User", "is_active": True}
            )
            ```
        """
        # Build filter conditions
        filters = []
        for k, v in kwargs.items():
            if hasattr(self.model, k):
                filters.append(getattr(self.model, k) == v)
        
        # Add tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            filters.append(self.model.tenant_id == tenant_id)
        
        # Try to get existing record
        if filters:
            query = select(self.model).where(and_(*filters))
            result = await session.execute(query)
            instance = result.scalar_one_or_none()
            
            if instance:
                return instance, False
        
        # Create new record
        create_data = {**kwargs}
        if defaults:
            create_data.update(defaults)
        
        if tenant_id and hasattr(self.model, "tenant_id"):
            create_data["tenant_id"] = tenant_id
        
        instance = self.model(**create_data)
        session.add(instance)
        
        try:
            await session.commit()
            await session.refresh(instance)
            return instance, True
        except IntegrityError as e:
            # Handle race condition - record might have been created
            await session.rollback()
            
            # Try to get the record again
            if filters:
                query = select(self.model).where(and_(*filters))
                result = await session.execute(query)
                instance = result.scalar_one_or_none()
                
                if instance:
                    return instance, False
            
            # If still not found, re-raise the error
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
    
    async def bulk_create(
        self,
        session: AsyncSession,
        *,
        objs_in: list[CreateSchemaType],
        tenant_id: Optional[str] = None,
        batch_size: int = 1000,
        return_models: bool = False,
    ) -> Union[list[ModelType], int]:
        """
        Create multiple records in bulk.
        
        Args:
            session: Database session.
            objs_in: List of Pydantic schemas with creation data.
            tenant_id: Optional tenant ID for multi-tenant records.
            batch_size: Number of records to insert per batch.
            return_models: If True, return created models; if False, return count.
        
        Returns:
            List of created model instances if return_models is True,
            otherwise the count of created records.
        
        Note:
            For very large datasets, this method processes records in
            batches to avoid memory issues. Set return_models=False
            for better performance with large datasets.
        """
        created_count = 0
        created_objs = [] if return_models else None
        
        # Process in batches
        for i in range(0, len(objs_in), batch_size):
            batch = objs_in[i:i + batch_size]
            
            db_objs = []
            for obj in batch:
                obj_data = obj.model_dump(exclude_unset=True)
                
                # Add tenant_id if multi-tenant
                if tenant_id and hasattr(self.model, "tenant_id"):
                    obj_data["tenant_id"] = tenant_id
                
                db_objs.append(self.model(**obj_data))
            
            session.add_all(db_objs)
            
            try:
                await session.commit()
                created_count += len(db_objs)
                
                if return_models:
                    # Refresh objects to get generated fields
                    for db_obj in db_objs:
                        await session.refresh(db_obj)
                    created_objs.extend(db_objs)
                    
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Failed bulk create at batch {i//batch_size}: {e}"
                )
                raise
        
        return created_objs if return_models else created_count
    
    async def bulk_update(
        self,
        session: AsyncSession,
        *,
        updates: list[dict[str, Any]],
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Update multiple records in bulk.
        
        Args:
            session: Database session.
            updates: List of dicts with 'id' and fields to update.
            tenant_id: Optional tenant ID for multi-tenant safety.
        
        Returns:
            Number of records updated.
        
        Example:
            ```python
            updates = [
                {"id": 1, "status": "active", "verified": True},
                {"id": 2, "status": "inactive"},
                {"id": 3, "name": "Updated Name"},
            ]
            count = await user_crud.bulk_update(session, updates=updates)
            ```
        """
        updated_count = 0
        
        for update_data in updates:
            if "id" not in update_data:
                logger.warning("Skipping update without 'id' field")
                continue
            
            obj_id = update_data.pop("id")
            
            if update_data:  # Only update if there are other fields
                db_obj = await self.get(session, obj_id, tenant_id=tenant_id)
                if db_obj:
                    for field, value in update_data.items():
                        if hasattr(db_obj, field):
                            setattr(db_obj, field, value)
                    
                    session.add(db_obj)
                    updated_count += 1
        
        if updated_count > 0:
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed bulk update: {e}")
                raise
        
        return updated_count
    
    async def search(
        self,
        session: AsyncSession,
        *,
        query: str,
        fields: list[str],
        skip: int = 0,
        limit: int = 100,
        tenant_id: Optional[str] = None,
    ) -> list[ModelType]:
        """
        Search records by text in multiple fields.
        
        Args:
            session: Database session.
            query: Search query string.
            fields: List of field names to search in.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            tenant_id: Optional tenant ID for multi-tenant filtering.
        
        Returns:
            List of matching model instances.
        
        Example:
            ```python
            # Search users by name or email
            results = await user_crud.search(
                session,
                query="john",
                fields=["name", "email"],
                limit=10
            )
            ```
        """
        search_query = select(self.model)
        
        # Build OR conditions for search fields
        search_conditions = []
        for field in fields:
            if hasattr(self.model, field):
                # Case-insensitive search using ILIKE (PostgreSQL)
                search_conditions.append(
                    getattr(self.model, field).ilike(f"%{query}%")
                )
        
        if search_conditions:
            search_query = search_query.where(or_(*search_conditions))
        
        # Apply tenant filter
        if tenant_id and hasattr(self.model, "tenant_id"):
            search_query = search_query.where(
                self.model.tenant_id == tenant_id
            )
        
        # Apply pagination
        search_query = search_query.offset(skip).limit(limit)
        
        result = await session.execute(search_query)
        return list(result.scalars().all())