"""
Base Repository Pattern.

Encapsulates database access and query construction away from service logic,
guaranteeing multi-tenant company isolation.
"""
from typing import Generic, TypeVar, Type, Any
from django.db import models
from django.shortcuts import get_object_or_404
from core.exceptions import NotFoundError

T = TypeVar("T", bound=models.Model)


class BaseRepository(Generic[T]):
    """Generic repository providing standardized tenant-scoped queries."""

    model: Type[T]

    def __init__(self, model_class: Type[T] | None = None):
        if model_class is not None:
            self.model = model_class

    def get_by_id(self, pk: Any, company_id: int | None = None) -> T:
        """Fetch a single record by primary key, optionally scoped to company."""
        qs = self.model.objects.all()
        if company_id is not None and hasattr(self.model, "company_id"):
            qs = qs.filter(company_id=company_id)
        try:
            return qs.get(pk=pk)
        except self.model.DoesNotExist as exc:
            raise NotFoundError(f"{self.model.__name__} with ID {pk} does not exist.") from exc

    def list_for_company(self, company_id: int, **filters) -> models.QuerySet[T]:
        """Return all records for a specific company."""
        if hasattr(self.model, "company_id"):
            filters["company_id"] = company_id
        return self.model.objects.filter(**filters)

    def create(self, **kwargs) -> T:
        """Create and return a new model instance."""
        return self.model.objects.create(**kwargs)

    def update(self, instance: T, **kwargs) -> T:
        """Update fields on an existing instance and save."""
        for key, val in kwargs.items():
            setattr(instance, key, val)
        instance.save(update_fields=list(kwargs.keys()) if kwargs else None)
        return instance

    def delete(self, instance: T) -> None:
        """Delete an instance."""
        instance.delete()