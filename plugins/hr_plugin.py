"""
HR Plugin - Agent Layer for Human Resources Operations.

This module contains the LeaveBalanceAgent class that provides HR-related
functions exposed to the Semantic Kernel for natural language processing
and intelligent routing.
"""

from typing import Annotated

from semantic_kernel.functions import kernel_function


class LeaveBalanceAgent:
    """
    Agent responsible for handling employee leave balance inquiries.

    This agent provides functions for retrieving leave balance information
    for employees. It serves as the "Agent Layer" in the Digital Employee
    architecture, processing requests routed by the Conversation Orchestrator.

    Attributes:
        _leave_data: Mock leave balance data for demonstration purposes.
    """

    def __init__(self) -> None:
        """Initialize the LeaveBalanceAgent with mock leave data."""
        self._leave_data: dict[str, dict[str, int]] = {
            "E001": {
                "annual_leave": 15,
                "sick_leave": 10,
                "personal_leave": 3,
                "parental_leave": 0,
            },
            "E002": {
                "annual_leave": 20,
                "sick_leave": 8,
                "personal_leave": 2,
                "parental_leave": 12,
            },
            "E003": {
                "annual_leave": 12,
                "sick_leave": 10,
                "personal_leave": 5,
                "parental_leave": 0,
            },
        }

    @kernel_function(
        name="get_leave_balance",
        description="Retrieves the current leave balance for a specific employee. "
        "Returns the number of days remaining for each leave type including "
        "annual leave, sick leave, personal leave, and parental leave.",
    )
    def get_leave_balance(
        self,
        employee_id: Annotated[
            str,
            "The unique identifier of the employee (e.g., 'E001', 'E002'). "
            "This is required to look up the employee's leave balance.",
        ],
    ) -> str:
        """
        Retrieve the leave balance for a specified employee.

        This function looks up the employee's leave balance data and returns
        a formatted response containing all available leave types and their
        remaining days.

        Args:
            employee_id: The unique identifier of the employee.

        Returns:
            A formatted string containing the employee's leave balance
            information, or an error message if the employee is not found.

        Example:
            >>> agent = LeaveBalanceAgent()
            >>> result = agent.get_leave_balance("E001")
            >>> print(result)
            Leave Balance for Employee E001:
            - Annual Leave: 15 days
            - Sick Leave: 10 days
            - Personal Leave: 3 days
            - Parental Leave: 0 days
        """
        employee_id_upper = employee_id.upper().strip()

        if employee_id_upper not in self._leave_data:
            return (
                f"Employee '{employee_id}' not found in the system. "
                "Please verify the employee ID and try again."
            )

        balance = self._leave_data[employee_id_upper]

        return (
            f"Leave Balance for Employee {employee_id_upper}:\n"
            f"- Annual Leave: {balance['annual_leave']} days\n"
            f"- Sick Leave: {balance['sick_leave']} days\n"
            f"- Personal Leave: {balance['personal_leave']} days\n"
            f"- Parental Leave: {balance['parental_leave']} days"
        )

    @kernel_function(
        name="get_total_leave_days",
        description="Calculates the total number of leave days remaining for "
        "an employee across all leave types.",
    )
    def get_total_leave_days(
        self,
        employee_id: Annotated[
            str,
            "The unique identifier of the employee to calculate total leave for.",
        ],
    ) -> str:
        """
        Calculate the total remaining leave days for an employee.

        Args:
            employee_id: The unique identifier of the employee.

        Returns:
            A string with the total leave days or an error message.
        """
        employee_id_upper = employee_id.upper().strip()

        if employee_id_upper not in self._leave_data:
            return f"Employee '{employee_id}' not found in the system."

        balance = self._leave_data[employee_id_upper]
        total = sum(balance.values())

        return (
            f"Employee {employee_id_upper} has a total of {total} leave days "
            "remaining across all leave types."
        )

    @kernel_function(
        name="list_employees",
        description="Lists all employee IDs currently in the system. "
        "Useful for discovering available employees to query.",
    )
    def list_employees(self) -> str:
        """
        List all employee IDs available in the system.

        Returns:
            A formatted string listing all employee IDs.
        """
        employee_ids = sorted(self._leave_data.keys())
        return f"Available employees in the system: {', '.join(employee_ids)}"
