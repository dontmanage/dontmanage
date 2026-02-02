# Copyright (c) 2025, DontManage Technologies and contributors
# For license information, please see license.txt

# import dontmanage
from dontmanage.model.document import Document


class WorkflowTransitionTasks(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF
		from dontmanage.workflow.doctype.workflow_transition_task.workflow_transition_task import (
			WorkflowTransitionTask,
		)

		tasks: DF.Table[WorkflowTransitionTask]
	# end: auto-generated types

	pass
