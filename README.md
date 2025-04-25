# MCP iCal Server

<div align="center">

🗓️ Agent-Powered Calendar Management for macOS

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)

</div>

> This project is based on [Omar-V2/mcp-ical](https://github.com/Omar-V2/mcp-ical.git) with a reimplemented user interaction layer using an agent-based approach.

## 🌟 Overview

Transform how you interact with your macOS calendar using a dedicated AI agent! This MCP iCal server leverages the OpenAI Agent SDK to provide a single, powerful entry point for all your calendar operations.

Unlike traditional MCP implementations that expose multiple tools, this server uses an agent-based approach:
- 🧠 **Single Tool Interface**: Just one MCP tool (`send_to_calendar_agent`) that delegates to a specialized calendar agent
- 🤖 **Stateful Conversations**: The agent maintains context between requests in the same session
- 🔄 **Zero-Config Operation**: Natural language processing handled automatically by the specialized agent

```
You: "What's my schedule for next week?"
Claude: "Let me check that for you..."
[Calendar agent processes request and returns clean schedule]

You: "Add a lunch meeting with Sarah tomorrow at noon"
Claude: "Event created: Lunch with Sarah, tomorrow at 12:00 PM"
```

## ✨ Features

### 📅 Event Creation
Transform natural language into calendar events instantly!

```
"Schedule a team lunch next Thursday at 1 PM at Bistro Garden"
↓
📎 Created: Team Lunch
   📅 Thursday, 1:00 PM
   📍 Bistro Garden
```

#### Supported Features:
- Custom calendar selection
- Location and notes
- Smart reminders
- Recurring events

#### Power User Examples:
```
🔄 Recurring Events:
"Set up my weekly team sync every Monday at 9 AM with a 15-minute reminder"

📝 Detailed Events:
"Schedule a product review meeting tomorrow from 2-4 PM in the Engineering calendar, 
add notes about reviewing Q1 metrics, and remind me 1 hour before"

📱 Multi-Calendar Support:
"Add a dentist appointment to my Personal calendar for next Wednesday at 3 PM"
```

### 🔍 Smart Schedule Management & Availability
Quick access to your schedule with natural queries:

```
"What's on my calendar for next week?"
↓
📊 Shows your upcoming events with smart formatting

"When am I free to schedule a 2-hour meeting next Tuesday?"
↓
🕒 Available time slots found:
   • Tuesday 10:00 AM - 12:00 PM
   • Tuesday 2:00 PM - 4:00 PM
```

### ✏️ Intelligent Event Updates
Modify events naturally:

```
"Move tomorrow's team meeting to 3 PM instead"
↓
✨ Meeting rescheduled to 3:00 PM
```

#### Update Capabilities:
- Time and date modifications
- Calendar transfers
- Location updates
- Note additions
- Reminder adjustments
- Recurring pattern changes

### 📊 Calendar Management
- View all available calendars
- Smart calendar suggestions
- Seamless Google Calendar integration when configured with iCloud

> 💡 **Pro Tip**: Since you can create events in custom calendars, if you have your Google Calendar synced with your iCloud Calendar, you can use this MCP server to create events in your Google Calendar too! Just specify the google calendar when creating/updating events.

## 🚀 Quick Start

> 💡 **Note**: While these instructions focus on setting up the MCP server with Claude for Desktop, this server can be used with any MCP-compatible client. For more details on using different clients, see [the MCP documentation](https://modelcontextprotocol.io/quickstart/client).

### Prerequisites
- [uv package manager](https://github.com/astral-sh/uv)
- macOS with Calendar app configured
- An MCP client - [Claude for desktop](https://claude.ai/download) is recommended
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)

### Installation

Whilst this MCP server can be used with any MCP compatible client, the instructions below are for use with Claude for desktop.

1. **Clone and Setup**
```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-ical.git
cd mcp-ical

# Install dependencies
uv sync
```

2. **Configure Claude for Desktop with API Key**

Create or edit `~/Library/Application\ Support/Claude/claude_desktop_config.json` and include your OpenAI API key as an environment variable:

```json
{
    "mcpServers": {
        "mcp-ical": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/PARENT/FOLDER/mcp-ical",
                "run",
                "mcp-ical"
            ],
            "env": {
                "OPENAI_API_KEY": "your-api-key-here"
            }
        }
    }
}
```

3. **Launch Claude for Calendar Access**

> ⚠️ **Critical**: Claude must be launched from the terminal to properly request calendar permissions. Launching directly from Finder will not trigger the permissions prompt.

```bash
/Applications/Claude.app/Contents/MacOS/Claude
```

4. **Start Using!**
```
Try: "What's my schedule looking like for next week?"
```

> 🔑 **Note**: When you first use a calendar-related command, macOS will prompt for calendar access. This prompt will only appear if you launched Claude from the terminal as specified above.

## 🧪 Testing

> ⚠️ **Warning**: Tests will create temporary calendars and events. While cleanup is automatic, only run tests in development environments.

```bash
# Install dev dependencies
uv sync --dev

# Run test suite
uv run pytest tests
```

## 🧠 How It Works

This implementation uses a unique architecture:

1. A single MCP tool (`send_to_calendar_agent`) is exposed to the client
2. When invoked, this tool passes the request to a specialized calendar agent built with the OpenAI Agent SDK
3. The agent processes the natural language request and calls the appropriate calendar operations
4. Results are formatted and returned to the client

This approach offers several advantages:
- **Simplified client integration**: Only one tool to invoke
- **Improved context handling**: The agent maintains conversation state
- **More natural interactions**: The specialized agent understands calendar-specific terminology and intent

## ❓ How This Project Differs From The Original

This implementation maintains much of the core calendar functionality from [Omar-V2/mcp-ical](https://github.com/Omar-V2/mcp-ical.git) but completely reimplements the user interaction layer:

1. **Single Entry Point**: Instead of exposing multiple MCP tools directly to the client, we've implemented a single entry point that delegates to an OpenAI-powered agent
2. **Agent-Based Processing**: Added an OpenAI Agent to handle natural language understanding and translation to calendar operations
3. **Stateful Conversations**: Added conversation context tracking between requests in the same session
4. **Simplified Client Integration**: Clients only need to know about one tool instead of multiple calendar operations

The core calendar operations (event creation, listing, etc.) and macOS integration remain largely unchanged from the original implementation.

## 🐛 Known Issues

### Recurring Events
- Non-standard recurring schedules may not always be set correctly
- Better results with more powerful LLM models
- Reminder timing for recurring all-day events may be off by one day

## 🤝 Contributing

Feedback and contributions are welcomed! Here's how you can help:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📝 Acknowledgments

- **Original Project**: Based on [Omar-V2/mcp-ical](https://github.com/Omar-V2/mcp-ical.git) by [Omar-V2](https://github.com/Omar-V2)
- Built with [Model Context Protocol](https://modelcontextprotocol.io)
- Calendar integration built with [PyObjC](https://github.com/ronaldoussoren/pyobjc)
- Agent capabilities powered by [OpenAI Agent SDK](https://github.com/openai/openai-python)
