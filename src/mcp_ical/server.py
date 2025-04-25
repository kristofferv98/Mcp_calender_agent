#!/usr/bin/env python3
"""
Calendar MCP server — single-tool façade over a stateful Agent SDK assistant.

Run with:
    python server.py            # starts FastMCP on stdio

It exposes exactly **one** MCP tool: `send_to_calendar_agent`.
Nothing else changed; all @function_tool definitions and docstrings are
identical to the CLI version you were happy with.
"""
import sys
import os
import functools
import json
from datetime import datetime
from typing import List, Optional, Callable, Any, TypeVar, cast
from dataclasses import dataclass, field

from loguru import logger
from agents import Agent, Runner, function_tool
from mcp.server.fastmcp import FastMCP

from agents import set_default_openai_key

set_default_openai_key(os.getenv("OPENAI_API_KEY"))

# --------------------------------------------------------------------------
#  Set-up + logging
# --------------------------------------------------------------------------
os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(sys.stderr,
           format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
           level="INFO")
logger.add("logs/calendar_agent.log",
           rotation="500 MB",
           retention="10 days",
           format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}",
           level="DEBUG")

# --------------------------------------------------------------------------
#  Real calendar backend + models
# --------------------------------------------------------------------------
from .ical import CalendarManager
from .models import CreateEventRequest, UpdateEventRequest, RecurrenceRule, Event

_calendar_manager = CalendarManager()

# --------------------------------------------------------------------------
#  Tool-call logging decorator
# --------------------------------------------------------------------------
T = TypeVar("T")
def log_tool_usage(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        sig = ", ".join([*map(repr, args), *[f"{k}={v!r}" for k, v in kwargs.items()]])
        logger.debug(f"TOOL_CALL: {func.__name__}({sig})")
        try:
            res = func(*args, **kwargs)
            logger.debug(f"TOOL_RESULT: {func.__name__} -> {str(res)[:1000]}")
            return res
        except Exception as e:
            logger.error(f"TOOL_ERROR: {func.__name__} -> {e}")
            raise
    return cast(Callable[..., T], wrapper)

# --------------------------------------------------------------------------
#  == BEGIN: original tool functions with untouched docstrings ==============
# --------------------------------------------------------------------------
@function_tool
@log_tool_usage
def _list_calendars() -> str:
    """List all available calendars that can be used with calendar operations.

    Returns:
        A newline-separated list of calendar names.
    """
    try:
        names = _calendar_manager.list_calendar_names()
        if not names:
            return "No calendars found"
        return "Available calendars:\n" + "\n".join(f"- {name}" for name in names)
    except Exception as e:
        return f"Error listing calendars: {e}"

@function_tool
@log_tool_usage
def _list_events(
    start_date: str,
    end_date: str,
    calendar_name: Optional[str] = None,
) -> str:
    """List calendar events in a date range.

    The start_date should always use the time such that it represents the beginning of that day (00:00:00).
    The end_date should always use the time such that it represents the end of that day (23:59:59).
    This way, range based searches are always inclusive and can locate all events in that date range.

    Args:
        start_date: Start date in ISO8601 format (YYYY-MM-DDT00:00:00).
        end_date:   End date in ISO8601 format (YYYY-MM-DDT23:59:59).
        calendar_name: Optional calendar name to filter by

    Returns:
        A concatenated string of all found events or an informative message if none are found.
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError as e:
        return f"Error: Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS). Details: {e}"
    try:
        events = _calendar_manager.list_events(start, end, calendar_name)
        if not events:
            return "No events found in the specified date range"
        return "".join(str(event) + "\n" for event in events)
    except Exception as e:
        return f"Error listing events: {e}"

@function_tool
@log_tool_usage
def _create_event(
    title: str,
    start_time: str,
    end_time: str,
    calendar_name: Optional[str] = None,
    notes: Optional[str] = None,
    location: Optional[str] = None,
    all_day: Optional[bool] = None,
    reminder_offsets: Optional[List[int]] = None,
    recurrence_rule: Optional[dict] = None,
) -> str:
    """Create a new calendar event.

    Before using this tool, make sure to:
    1. Ask the user which calendar they want to use if not specified (_list_calendars)
    2. Ask if they want to add a location if none provided
    3. Ask if they want to add any notes/description if none provided
    4. Confirm the date and time with the user
    5. Ask if they want to set reminders for the event

    Args:
        title: Event title
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        calendar_name: Optional calendar (defaults to manager default)
        notes: Optional event notes/description
        location: Optional event location
        all_day: Whether this is an all-day event
        reminder_offsets: List of minutes before the event to trigger reminders
        recurrence_rule: Optional dict to build a RecurrenceRule model

    Returns:
        Success or error message including new event ID.
    """
    try:
        req = CreateEventRequest(
            title=title,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            calendar_name=calendar_name,
            notes=notes,
            location=location,
            all_day=all_day if all_day is not None else False,
            reminder_offsets=reminder_offsets or [],
            recurrence_rule=RecurrenceRule(**recurrence_rule) if recurrence_rule else None,
        )
        ev = _calendar_manager.create_event(req)
        return f"Successfully created event: {ev.title} (ID: {ev.identifier})"
    except Exception as e:
        return f"Error creating event: {e}"

@function_tool
@log_tool_usage
def _update_event(
    event_id: str,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    notes: Optional[str] = None,
    location: Optional[str] = None,
    calendar_name: Optional[str] = None,
    all_day: Optional[bool] = None,
    reminder_offsets: Optional[List[int]] = None,
    recurrence_rule: Optional[dict] = None,
) -> str:
    """Update an existing calendar event.

    Before using this tool, make sure to:
    1. Ask the user which fields they want to update
    2. If moving to a different calendar, verify it exists (_list_calendars)
    3. If updating time, confirm the new time with the user
    4. Ask if they want to add/update location if not specified
    5. Ask if they want to add/update notes if not specified
    6. Ask if they want to set reminders for the event

    Args:
        event_id: Unique identifier of the event to update
        title: Optional new title
        start_time: Optional new start time in ISO format
        end_time: Optional new end time in ISO format
        notes: Optional new notes/description
        location: Optional new location
        calendar_name: Optional new calendar
        all_day: Optional all-day flag
        reminder_offsets: List of minutes before the event to trigger reminders
        recurrence_rule: Optional dict to build a RecurrenceRule model

    Returns:
        Success or error message reflecting the update.
    """
    try:
        req = UpdateEventRequest(
            title=title,
            start_time=datetime.fromisoformat(start_time) if start_time else None,
            end_time=datetime.fromisoformat(end_time) if end_time else None,
            notes=notes,
            location=location,
            calendar_name=calendar_name,
            all_day=all_day,
            reminder_offsets=reminder_offsets,
            recurrence_rule=RecurrenceRule(**recurrence_rule) if recurrence_rule else None,
        )
        ev = _calendar_manager.update_event(event_id, req)
        if not ev:
            return f"Failed to update event: ID {event_id} not found"
        return f"Successfully updated event: {ev.title}"
    except Exception as e:
        return f"Error updating event: {e}"

@function_tool
@log_tool_usage
def _delete_event(
    event_id: str = None,
    event_ids: List[str] = None,
) -> str:
    """Delete one or more existing calendar events.

    Before using this tool, make sure to:
    1. Get and confirm the exact event ID(s) to delete
    2. Ask the user for confirmation before deletion

    Args:
        event_id: Unique identifier of a single event to delete
        event_ids: List of up to 10 event IDs to delete in a single operation

    Returns:
        Success or error message reflecting the deletion results.
    """
    # Handle the case where both are None
    if event_id is None and not event_ids:
        return "Error: You must provide either event_id or event_ids parameter"
    
    # Handle single event deletion (backward compatibility)
    if event_id and not event_ids:
        try:
            success = _calendar_manager.delete_event(event_id)
            if success:
                return f"Successfully deleted event with ID: {event_id}"
            return f"Failed to delete event: ID {event_id} not found"
        except Exception as e:
            return f"Error deleting event: {e}"
    
    # Handle multiple event deletion
    ids_to_delete = event_ids or [event_id]
    
    # Limit to 10 events for safety
    if len(ids_to_delete) > 10:
        return f"Error: Cannot delete more than 10 events at once. Received {len(ids_to_delete)} event IDs."
    
    results = []
    for eid in ids_to_delete:
        try:
            success = _calendar_manager.delete_event(eid)
            if success:
                results.append(f"✓ ID {eid}: Successfully deleted")
            else:
                results.append(f"✗ ID {eid}: Not found")
        except Exception as e:
            results.append(f"✗ ID {eid}: Error - {e}")
    
    # Format the results as a readable message
    if len(results) == 1:
        return results[0]
    
    summary = f"Deleted {len([r for r in results if r.startswith('✓')])} of {len(ids_to_delete)} events:"
    return f"{summary}\n" + "\n".join(results)

# --------------------------------------------------------------------------
#  == END: original tool functions ==========================================
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
#  Agent builder with dynamic date
# --------------------------------------------------------------------------
def _build_calendar_agent() -> Agent:
    return Agent(
        name="CalendarAgent",
        instructions=(
            f"[Current date: {datetime.now().date()}]\n"
            "You are a deterministic calendar assistant. "
            "Use ONLY the provided tools. "
            "Never greet, never volunteer suggestions."
        ),
        model="o4-mini",
        tools=[_list_calendars, _list_events, _create_event, _update_event, _delete_event],
    )

# --------------------------------------------------------------------------
#  Conversation context + helper
# --------------------------------------------------------------------------
@dataclass
class SessionCtx:
    username: str = "User"
    conversation: list[dict] = field(default_factory=list)

# ---------------------------------------------------------------------
#  Prefix injected at the start of every *new* conversation turn
# ---------------------------------------------------------------------
AGENT_START_PREFIX = """
You are the CalendarAgent router. Obey these rules **exactly**:

1. **Permitted commands** (must appear _first_ in the message):
   • list_calendars
   • list_events      start_date=… end_date=… [calendar_name=…]
   • create_event     title=… start_time=… end_time=… [optional args]
   • update_event     event_id=… [optional args]
   • delete_event     event_id=… | event_ids=[id1,id2,…]

2. **Clarification**  
   – If any required field is missing or ambiguous, ask _precisely one_ follow-up.  
   – If the user's intent is still unclear after that, respond:  
        `Error: insufficient information to fulfil request.`

3. **Tool execution**  
   – Call the matching tool immediately after you have all required data.  
   – Never invent or transform parameters; use them verbatim.

4. **Output formatting**  
   – Return **exactly** the raw tool output, unchanged and unabridged.  
   – Prefix the output with a short status line, e.g.  
        `OK – events listed:` or `FAILED – error from calendar service:`  
     so the user instantly knows success/failure.

5. **Style constraints**  
   – No greetings, small-talk, or unsolicited suggestions.  
   – No self-reference ("as an AI").  
   – No apologies unless a tool call genuinely fails.

6. **Always spesify what information is from which calender**
   - Always spesify what calender information asre from when listing events.
   - Always spesify what calender the event is in when creating, updating or deleting an event.
   - Always spesify the id of the event when updating or deleting an event.

Remember: the user cannot see internal tool calls—your reply _is_ the tool output.
""".strip()

async def _one_turn(msg: str, *, reset: bool,
                    agent: Agent, ctx: SessionCtx) -> str:
    if reset:
        ctx.conversation.clear()
        # Only inject the prefix when specifically requested to reset
        if "list_calendars" in msg or "list_events" in msg or "create_event" in msg or "update_event" in msg or "delete_event" in msg:
            msg = f"{AGENT_START_PREFIX}\n\n{msg}"
    ctx.conversation.append({"role": "user", "content": msg})
    result = await Runner.run(starting_agent=agent, input=ctx.conversation, context=ctx)
    ctx.conversation = result.to_input_list()
    return result.final_output

# --------------------------------------------------------------------------
#  MCP façade
# --------------------------------------------------------------------------
mcp = FastMCP("Calendar")
_agent_inst: Agent | None = None
_ctx_inst: SessionCtx | None = None

@mcp.tool()
async def send_to_calendar_agent(message: str, start_conversation: bool = False) -> str:
    """Calendar assistant tool for direct calendar operations.

    A single entry point for all calendar operations. Communicates with a specialized 
    calendar agent that handles list, create, update, and delete operations.
    You should not create, update, or delete anything without the users direct 
    confirmation or specification. The agent is highly intelligent and autonomous
    and will only do what you tell it to do. You can spesify many different requests in one message 
    to the agent, it will handle them one by one.
    
    Parameters
    ----------
    message : str
        Command that MUST start with one of:
        • list_events start_date=YYYY-MM-DDT00:00:00 end_date=YYYY-MM-DDT23:59:59 [calendar_name=...]
        • create_event title=... start_time=... end_time=... [notes=...] [location=...] [calendar_name=...]
        • update_event event_id=... [optional field changes]
        • delete_event event_ids=[id1,id2,...] - Deletes one or more events by their ids

    start_conversation : bool, default False
        When True, starts a new conversation context. Use for new tasks.

    Returns
    -------
    str
        Brief response with results or confirmation. Never conversational.
    """
    global _agent_inst, _ctx_inst
    if start_conversation or _agent_inst is None:
        _agent_inst = _build_calendar_agent()
        _ctx_inst = SessionCtx()
    return await _one_turn(message, reset=start_conversation, agent=_agent_inst, ctx=_ctx_inst)

# --------------------------------------------------------------------------
#  Server entry-point
# --------------------------------------------------------------------------
def main() -> None:
    logger.info("Running MCP Calendar server — only send_to_calendar_agent tool exposed.")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()