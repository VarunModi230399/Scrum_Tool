from src.modules.projects.application.ports import WorkItemRepository
from src.modules.projects.domain.entities import WorkItem, WorkItemStatus


def compute_own_progress(work_item: WorkItem, children: list[WorkItem]) -> float:
    """Weighted average of children's effective progress (by story points, else equal weight).

    Leaf items (no children) derive progress from status: 100 if done, else 0.
    """
    if children:
        weighted_total = 0.0
        weight_sum = 0.0
        for child in children:
            weight = child.story_points if child.story_points else 1.0
            weighted_total += weight * child.effective_progress
            weight_sum += weight
        return weighted_total / weight_sum if weight_sum else 0.0
    return 100.0 if work_item.status == WorkItemStatus.DONE else 0.0


class ProgressRollupService:
    """Recomputes a work item's own progress and cascades the change up its ancestor chain.

    Synchronous and bounded by tree depth — simpler and more testable than the
    async Celery cascade sketched in ARCHITECTURE.md, which is deferred until
    tree sizes actually justify it (see ARCHITECTURE.md §8).
    """

    def __init__(self, work_item_repo: WorkItemRepository):
        self._work_items = work_item_repo

    async def recompute(self, work_item: WorkItem) -> None:
        current: WorkItem | None = work_item
        while current is not None:
            if current.progress_override is None:
                children = await self._work_items.list_children(current.id)
                computed = compute_own_progress(current, children)
                current = await self._work_items.set_progress(current.id, computed)
            if current.parent_id is None:
                return
            current = await self._work_items.get_by_id(current.parent_id)
