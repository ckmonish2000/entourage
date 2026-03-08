# Plan: Autonomous Sub-agents Architecture

This document outlines the strategy for implementing autonomous sub-agents within the Entourage framework. The goal is to enable a "Planner" agent to delegate complex sub-tasks to specialized "Worker" agents that operate independently, while also supporting simple standalone execution for straightforward tasks.

## 1. High-Level Workflow

### 1.1 Standalone Mode (Simple Tasks)
For straightforward tasks that don't require complex coordination:

1.  **Direct Execution**: User request goes directly to a single specialized agent
2.  **Task Completion**: Agent executes the task using available tools
3.  **Result Delivery**: Agent returns results directly to the user
4.  **Use Cases**: Single-file edits, simple queries, focused operations

### 1.2 Sub-agent Mode (Complex Tasks)
For complex tasks requiring coordination and specialization:

1.  **Triage/Planning Phase**: The main Entourage agent (Planner) receives a user request and generates a comprehensive `PROJECT_PLAN.md`
2.  **Task Identification**: The Planner identifies specific, self-contained tasks within the plan that can be delegated (e.g., "Implement Frontend Components", "Setup Database Schema")
3.  **Spawning Sub-agents**: The Planner uses the `delegate` tool to spawn specialized sub-agents
4.  **Autonomous Execution with Visibility**:
    - The sub-agent receives its task and role
    - Executes autonomously using its own conversation context
    - **Conversation thread is streamed to user in real-time**
    - **User can provide mid-execution feedback to steer direction**
5.  **Reporting & Integration**: Once the sub-agent completes its task, it returns a summary of its accomplishments to the Planner. The Planner validates the work and updates the `PROJECT_PLAN.md`

## 2. Technical Components

### A. Execution Mode Router
A decision layer that determines whether to use standalone or sub-agent mode:

**Location**: `agents/core/router.py`

```python
class ExecutionRouter:
    @staticmethod
    def should_delegate(task: str, complexity_score: float) -> bool:
        """
        Determines if task requires sub-agent delegation

        Args:
            task: User request description
            complexity_score: 0.0-1.0 score based on:
                - Number of files to modify (>5 files = higher score)
                - Cross-domain requirements (frontend + backend = higher)
                - Number of distinct operations (>3 operations = higher)

        Returns:
            True if sub-agent mode needed, False for standalone
        """
        # Simple heuristics
        if complexity_score < 0.3:
            return False  # Standalone mode
        return True  # Sub-agent mode
```

**Integration Point**: Main agent checks this before deciding execution strategy

### B. The `delegate` Tool (Sub-agent Mode)

**Location**: `agents/tools/builtin/delegate.py`

**Function Signature**:
```python
def delegate(task: str, role: str, stream_to_user: bool = True) -> dict
```

**Parameters**:
- `task`: Clear, specific instruction for the sub-agent (e.g., "Implement user authentication API endpoints")
- `role`: Specialized role identifier (e.g., "backend_developer", "frontend_engineer", "database_architect")
- `stream_to_user`: Whether to stream conversation to user in real-time (default: True)

**Return Value**:
```python
{
    "status": "completed" | "failed" | "interrupted",
    "summary": "Human-readable summary of work done",
    "files_modified": ["path/to/file1.py", "path/to/file2.js"],
    "files_created": ["path/to/new_file.py"],
    "execution_log": "Full conversation thread",
    "user_interventions": [
        {"timestamp": "2025-01-15T10:30:00", "instruction": "Use JWT instead of sessions"}
    ]
}
```

**Logic Flow**:
```python
def delegate(task: str, role: str, stream_to_user: bool = True) -> dict:
    # 1. Generate unique session ID
    session_id = f"subagent_{role}_{uuid.uuid4()}"

    # 2. Construct specialized system prompt
    system_prompt = ROLE_TEMPLATES[role].format(task=task)

    # 3. Initialize sub-agent with streaming
    agent = Agent(
        session_id=session_id,
        system_prompt=system_prompt,
        enable_streaming=stream_to_user
    )

    # 4. Create bidirectional communication channel
    user_input_queue = Queue()  # For mid-execution user input
    agent_output_stream = Queue()  # For streaming to user

    # 5. Execute task with user visibility
    result = agent.process_message_with_feedback(
        task=task,
        user_input_queue=user_input_queue,
        output_stream=agent_output_stream
    )

    # 6. Return structured result
    return {
        "status": result.status,
        "summary": result.summary,
        "files_modified": result.files_modified,
        "files_created": result.files_created,
        "execution_log": result.full_conversation,
        "user_interventions": result.user_interventions
    }
```

### C. Agent Core Enhancements

#### C.1 Streaming with User Feedback
**Location**: `agents/core/agent.py`

**New Method**: `process_message_with_feedback()`
```python
def process_message_with_feedback(
    self,
    task: str,
    user_input_queue: Queue,
    output_stream: Queue
) -> ExecutionResult:
    """
    Execute task with real-time user visibility and feedback capability

    Args:
        task: Task to execute
        user_input_queue: Queue for receiving user interruptions
        output_stream: Queue for streaming execution to user

    Flow:
        1. Add task to conversation history
        2. Loop until task complete:
            a. Generate next response
            b. Stream response to output_stream
            c. Check user_input_queue for interventions
            d. If user input exists, inject into conversation
            e. Execute tools if needed
            f. Continue
        3. Return structured result
    """
    pass  # Implementation details below
```

**Key Features**:
- **Real-time streaming**: Every agent thought, tool call, and result goes to `output_stream`
- **User interruption**: Check `user_input_queue` after each agent turn
- **Context preservation**: User feedback becomes part of conversation history

#### C.2 Non-Streaming Fallback
For scenarios where streaming isn't needed:
```python
def process_message(self, task: str, stream: bool = False) -> str:
    """
    Original method for backward compatibility
    If stream=False, execute without user visibility
    """
    pass
```

### D. User Interface Integration

#### D.1 CLI Display (for terminal users)
**Location**: `cli/display.py`

```python
class SubAgentDisplay:
    """Handles real-time display of sub-agent execution"""

    def show_execution_stream(self, agent_id: str, output_stream: Queue):
        """
        Display streaming output with visual separation

        Format:
        ┌─ Sub-Agent: backend_developer ─────────────────┐
        │ [THOUGHT] Analyzing authentication requirements│
        │ [TOOL] read_file(path="auth/config.py")        │
        │ [RESULT] Found existing auth configuration     │
        │ [USER_INPUT] ⚠ Use JWT instead of sessions    │
        │ [THOUGHT] Switching to JWT implementation      │
        └────────────────────────────────────────────────┘
        """
        pass

    def prompt_for_intervention(self) -> str | None:
        """
        Non-blocking check for user input
        Returns user instruction if provided, None otherwise
        """
        pass
```

#### D.2 User Intervention Flow
```python
# In main CLI loop
while subagent.is_running():
    # Display stream
    display.show_execution_stream(subagent.id, output_stream)

    # Check for user input (non-blocking)
    user_input = display.prompt_for_intervention()
    if user_input:
        user_input_queue.put({
            "timestamp": datetime.now(),
            "instruction": user_input,
            "type": "course_correction"
        })
        print(f"✓ Feedback sent to sub-agent")
```

### E. Standalone Execution Mode

**Location**: `agents/core/standalone.py`

```python
class StandaloneAgent:
    """
    Simplified agent for direct task execution
    No planning, no delegation, just execute and return
    """

    def execute(self, task: str, role: str) -> str:
        """
        Direct execution without sub-agent overhead

        Args:
            task: Task to complete
            role: Agent specialization (same role system as sub-agents)

        Returns:
            Simple text result
        """
        agent = Agent(
            session_id=f"standalone_{uuid.uuid4()}",
            system_prompt=ROLE_TEMPLATES[role],
            enable_streaming=True  # Still show progress to user
        )

        result = agent.process_message(task, stream=True)
        return result
```

**Usage Example**:
```python
# User: "Fix the typo in README.md line 15"
# System: Detects low complexity, uses standalone mode
standalone_agent = StandaloneAgent()
result = standalone_agent.execute(
    task="Fix the typo in README.md line 15",
    role="editor"
)
# Result: Direct execution, no planning overhead
```

### F. Communication Protocol

#### F.1 Input Format
**To Sub-agent**:
```python
{
    "task": "Implement user authentication API endpoints",
    "role": "backend_developer",
    "context": {
        "existing_files": ["auth/models.py", "auth/views.py"],
        "dependencies": ["Django", "djangorestframework"],
        "constraints": ["Must use JWT", "Follow existing patterns"]
    }
}
```

#### F.2 Output Format
**From Sub-agent**:
```python
{
    "status": "completed",
    "summary": "Created 3 API endpoints: /login, /register, /refresh-token. Implemented JWT authentication with 30min access tokens and 7-day refresh tokens.",
    "files_modified": ["auth/views.py", "auth/serializers.py"],
    "files_created": ["auth/jwt_utils.py", "tests/test_auth_api.py"],
    "execution_log": "Full conversation thread...",
    "user_interventions": [
        {
            "timestamp": "2025-01-15T10:30:00",
            "instruction": "Use JWT instead of sessions",
            "agent_response": "Understood. Switching implementation to JWT tokens."
        }
    ],
    "tests_passed": true,
    "coverage": "95%"
}
```

## 3. Implementation Steps

### Phase 1: Core Infrastructure (Week 1-2)

#### Step 1: Execution Mode Router
**File**: `agents/core/router.py`
**Priority**: High
**Estimated Time**: 2 days

**Tasks**:
1. Create `ExecutionRouter` class with `should_delegate()` method
2. Implement complexity scoring algorithm:
   ```python
   def calculate_complexity(task: str) -> float:
       score = 0.0
       # File count analysis
       file_mentions = count_file_references(task)
       if file_mentions > 5:
           score += 0.3
       # Cross-domain keywords
       if has_keywords(task, ["frontend", "backend", "database"]):
           score += 0.3
       # Operation count
       operations = count_operations(task)  # create, update, delete, test
       if operations > 3:
           score += 0.4
       return min(score, 1.0)
   ```
3. Write unit tests for complexity scoring
4. Integrate into main agent decision flow

**Testing**:
```python
# Test cases
assert should_delegate("Fix typo in README", 0.1) == False
assert should_delegate("Build auth system with JWT", 0.8) == True
```

#### Step 2: Standalone Execution Mode
**File**: `agents/core/standalone.py`
**Priority**: High
**Estimated Time**: 3 days

**Tasks**:
1. Create `StandaloneAgent` class
2. Implement `execute()` method with streaming
3. Reuse existing `Agent` core but skip planning overhead
4. Add role templates for standalone agents
5. Create CLI integration for standalone mode

**Code Structure**:
```python
# agents/core/standalone.py
from agents.core.agent import Agent
from agents.core.roles import ROLE_TEMPLATES

class StandaloneAgent:
    def __init__(self):
        self.agent = None

    def execute(self, task: str, role: str = "generalist") -> str:
        session_id = f"standalone_{uuid.uuid4()}"
        self.agent = Agent(
            session_id=session_id,
            system_prompt=ROLE_TEMPLATES.get(role, ROLE_TEMPLATES["generalist"]),
            enable_streaming=True
        )
        return self.agent.process_message(task, stream=True)
```

**Testing**:
- Test with simple tasks (single file edits, queries)
- Verify streaming works
- Ensure no planning overhead

#### Step 3: Agent Core Streaming Enhancement
**File**: `agents/core/agent.py`
**Priority**: Critical
**Estimated Time**: 5 days

**Tasks**:
1. Add `process_message_with_feedback()` method
2. Implement bidirectional queue communication
3. Add user intervention handling in agent loop
4. Ensure conversation history preserves user feedback
5. Handle edge cases (queue timeouts, invalid input)

**Detailed Implementation**:
```python
# agents/core/agent.py
from queue import Queue, Empty
from datetime import datetime

class Agent:
    def process_message_with_feedback(
        self,
        task: str,
        user_input_queue: Queue,
        output_stream: Queue,
        check_interval: float = 0.5  # Check for user input every 0.5s
    ) -> ExecutionResult:
        # Initialize
        self.conversation_history.append({"role": "user", "content": task})
        user_interventions = []
        files_modified = set()
        files_created = set()

        # Main execution loop
        while not self._is_task_complete():
            # Generate next agent response
            response = self._generate_response(stream=True)

            # Stream to user
            output_stream.put({
                "type": "thought",
                "content": response.text,
                "timestamp": datetime.now()
            })

            # Check for user intervention (non-blocking)
            try:
                user_intervention = user_input_queue.get(timeout=check_interval)
                # Inject user feedback into conversation
                intervention_msg = f"[USER FEEDBACK]: {user_intervention['instruction']}"
                self.conversation_history.append({
                    "role": "user",
                    "content": intervention_msg
                })
                user_interventions.append(user_intervention)

                output_stream.put({
                    "type": "user_intervention",
                    "content": user_intervention['instruction'],
                    "timestamp": user_intervention['timestamp']
                })
            except Empty:
                pass  # No user input, continue

            # Execute tools if needed
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    output_stream.put({
                        "type": "tool_call",
                        "tool": tool_call.name,
                        "args": tool_call.arguments,
                        "timestamp": datetime.now()
                    })

                    result = self._execute_tool(tool_call)

                    # Track file operations
                    if tool_call.name in ["write_file", "edit_file"]:
                        files_modified.add(tool_call.arguments.get("path"))
                    if tool_call.name == "write_file":
                        files_created.add(tool_call.arguments.get("path"))

                    output_stream.put({
                        "type": "tool_result",
                        "content": result,
                        "timestamp": datetime.now()
                    })

        # Generate final summary
        summary = self._generate_summary()

        return ExecutionResult(
            status="completed",
            summary=summary,
            files_modified=list(files_modified),
            files_created=list(files_created),
            execution_log=self._get_full_conversation(),
            user_interventions=user_interventions
        )

    def _is_task_complete(self) -> bool:
        """
        Determine if task is complete
        Can be based on:
        - Agent explicitly states completion
        - No more tool calls needed
        - User intervention indicates completion
        """
        # Check last assistant message for completion indicators
        if not self.conversation_history:
            return False

        last_msg = self.conversation_history[-1]
        if last_msg["role"] == "assistant":
            completion_phrases = [
                "task completed",
                "finished",
                "done with",
                "successfully implemented"
            ]
            return any(phrase in last_msg["content"].lower() for phrase in completion_phrases)

        return False
```

**Testing**:
- Test without user intervention (normal flow)
- Test with mid-execution user feedback
- Test with multiple interventions
- Test edge cases (empty queue, rapid interventions)

### Phase 2: Delegation System (Week 3-4)

#### Step 4: Delegate Tool Implementation
**File**: `agents/tools/builtin/delegate.py`
**Priority**: Critical
**Estimated Time**: 4 days

**Tasks**:
1. Create `delegate()` function with full signature
2. Implement role-based system prompt generation
3. Integrate with `process_message_with_feedback()`
4. Add comprehensive error handling
5. Register tool in tool registry

**Full Implementation**:
```python
# agents/tools/builtin/delegate.py
import uuid
from queue import Queue
from typing import Dict, Any
from agents.core.agent import Agent, ExecutionResult
from agents.core.roles import ROLE_TEMPLATES

def delegate(task: str, role: str, stream_to_user: bool = True) -> Dict[str, Any]:
    """
    Delegate task to specialized sub-agent

    Args:
        task: Clear task description
        role: Specialized role (backend_developer, frontend_engineer, etc.)
        stream_to_user: Enable real-time streaming and user feedback

    Returns:
        Execution result dictionary with status, summary, files, etc.

    Raises:
        ValueError: If role not found in ROLE_TEMPLATES
        RuntimeError: If sub-agent execution fails
    """
    # Validate role
    if role not in ROLE_TEMPLATES:
        raise ValueError(f"Unknown role: {role}. Available: {list(ROLE_TEMPLATES.keys())}")

    # Generate session ID
    session_id = f"subagent_{role}_{uuid.uuid4()}"

    # Get specialized system prompt
    system_prompt = ROLE_TEMPLATES[role].format(task=task)

    # Initialize sub-agent
    agent = Agent(
        session_id=session_id,
        system_prompt=system_prompt,
        enable_streaming=stream_to_user
    )

    # Create communication channels
    user_input_queue = Queue()
    agent_output_stream = Queue()

    try:
        # Execute with feedback capability
        result = agent.process_message_with_feedback(
            task=task,
            user_input_queue=user_input_queue,
            output_stream=agent_output_stream
        )

        return {
            "status": result.status,
            "summary": result.summary,
            "files_modified": result.files_modified,
            "files_created": result.files_created,
            "execution_log": result.full_conversation,
            "user_interventions": result.user_interventions
        }

    except Exception as e:
        return {
            "status": "failed",
            "summary": f"Sub-agent execution failed: {str(e)}",
            "files_modified": [],
            "files_created": [],
            "execution_log": agent._get_full_conversation(),
            "user_interventions": [],
            "error": str(e)
        }

# Tool metadata for registry
TOOL_METADATA = {
    "name": "delegate",
    "description": "Delegate complex task to specialized sub-agent",
    "parameters": {
        "task": {"type": "string", "required": True},
        "role": {"type": "string", "required": True},
        "stream_to_user": {"type": "boolean", "required": False, "default": True}
    }
}
```

**Testing**:
- Test delegation with different roles
- Test with and without streaming
- Test error handling (invalid role, execution failure)
- Verify result format matches specification

#### Step 5: Role Templates System
**File**: `agents/core/roles.py`
**Priority**: High
**Estimated Time**: 3 days

**Tasks**:
1. Define role templates for different specializations
2. Create template formatting system
3. Add role-specific tool permissions
4. Document each role's capabilities

**Implementation**:
```python
# agents/core/roles.py
ROLE_TEMPLATES = {
    "backend_developer": """You are a specialized backend developer sub-agent.

Task: {task}

Capabilities:
- Implement API endpoints and business logic
- Design database schemas
- Write backend tests
- Configure server settings

Tools Available: read_file, write_file, edit_file, shell, list_directory

Constraints:
- Follow RESTful API design principles
- Write comprehensive tests for all endpoints
- Use existing project patterns and dependencies
- Document API endpoints

Output Requirements:
When task is complete, provide:
1. Summary of implementation
2. List of files modified/created
3. Test results
4. Any issues or recommendations
""",

    "frontend_engineer": """You are a specialized frontend engineer sub-agent.

Task: {task}

Capabilities:
- Build UI components
- Implement client-side logic
- Style responsive interfaces
- Integrate with APIs

Tools Available: read_file, write_file, edit_file, list_directory

Constraints:
- Follow component library patterns
- Ensure mobile responsiveness
- Write component tests
- Follow accessibility guidelines (WCAG 2.1)

Output Requirements:
When task is complete, provide:
1. Summary of components created
2. List of files modified/created
3. Component test results
4. Browser compatibility notes
""",

    "database_architect": """You are a specialized database architect sub-agent.

Task: {task}

Capabilities:
- Design database schemas
- Write migrations
- Optimize queries
- Ensure data integrity

Tools Available: read_file, write_file, edit_file, shell

Constraints:
- Follow normalization principles
- Add appropriate indexes
- Write reversible migrations
- Document schema decisions

Output Requirements:
When task is complete, provide:
1. Schema design summary
2. Migration files created
3. Performance considerations
4. Data integrity constraints
""",

    "test_engineer": """You are a specialized test engineer sub-agent.

Task: {task}

Capabilities:
- Write unit tests
- Create integration tests
- Implement E2E tests
- Measure code coverage

Tools Available: read_file, write_file, edit_file, shell

Constraints:
- Achieve >80% code coverage
- Test edge cases and error conditions
- Use existing test framework
- Follow AAA pattern (Arrange, Act, Assert)

Output Requirements:
When task is complete, provide:
1. Test summary with coverage metrics
2. List of test files created
3. Test results
4. Coverage gaps identified
""",

    "generalist": """You are a versatile generalist agent.

Task: {task}

Capabilities:
- Handle diverse tasks across domains
- Adapt approach based on requirements
- Use all available tools

Tools Available: read_file, write_file, edit_file, shell, list_directory

Output Requirements:
When task is complete, provide:
1. Summary of work completed
2. Files modified/created
3. Any relevant notes or recommendations
"""
}

def get_role_tools(role: str) -> list[str]:
    """Get allowed tools for specific role"""
    role_tools = {
        "backend_developer": ["read_file", "write_file", "edit_file", "shell", "list_directory"],
        "frontend_engineer": ["read_file", "write_file", "edit_file", "list_directory"],
        "database_architect": ["read_file", "write_file", "edit_file", "shell"],
        "test_engineer": ["read_file", "write_file", "edit_file", "shell"],
        "generalist": ["read_file", "write_file", "edit_file", "shell", "list_directory"]
    }
    return role_tools.get(role, role_tools["generalist"])
```

### Phase 3: User Interface (Week 5)

#### Step 6: CLI Display System
**File**: `cli/display.py`
**Priority**: Medium
**Estimated Time**: 4 days

**Tasks**:
1. Create `SubAgentDisplay` class
2. Implement streaming output display
3. Add non-blocking user input prompt
4. Design visual formatting for different event types
5. Add color coding and progress indicators

**Implementation**:
```python
# cli/display.py
import sys
from queue import Queue, Empty
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

class SubAgentDisplay:
    def __init__(self):
        self.console = Console()

    def show_execution_stream(self, agent_id: str, output_stream: Queue, role: str):
        """Display streaming output with visual formatting"""
        with Live(console=self.console, refresh_per_second=4) as live:
            logs = []

            while True:
                try:
                    event = output_stream.get(timeout=0.1)

                    if event["type"] == "thought":
                        logs.append(f"[cyan]💭 THOUGHT:[/] {event['content']}")
                    elif event["type"] == "tool_call":
                        logs.append(f"[yellow]🔧 TOOL:[/] {event['tool']}({event['args']})")
                    elif event["type"] == "tool_result":
                        logs.append(f"[green]✓ RESULT:[/] {event['content'][:100]}...")
                    elif event["type"] == "user_intervention":
                        logs.append(f"[red]⚠️  USER:[/] {event['content']}")
                    elif event["type"] == "completion":
                        logs.append(f"[bold green]✅ COMPLETE[/]")
                        break

                    # Update display
                    panel_content = "\n".join(logs[-20:])  # Show last 20 lines
                    panel = Panel(
                        panel_content,
                        title=f"Sub-Agent: {role}",
                        border_style="blue"
                    )
                    live.update(panel)

                except Empty:
                    continue
                except Exception as e:
                    logs.append(f"[red]ERROR: {e}[/]")
                    break

    def prompt_for_intervention(self) -> str | None:
        """Non-blocking check for user input"""
        # Use select to check stdin without blocking
        import select

        # Check if input is available (timeout = 0 for non-blocking)
        if select.select([sys.stdin], [], [], 0)[0]:
            user_input = input("\n[FEEDBACK] > ")
            return user_input
        return None
```

**Testing**:
- Test display with different event types
- Verify non-blocking input works
- Test visual formatting on different terminals

#### Step 7: Main CLI Integration
**File**: `cli/main.py`
**Priority**: High
**Estimated Time**: 3 days

**Tasks**:
1. Integrate `ExecutionRouter` into main CLI flow
2. Add sub-agent execution loop with display
3. Implement user intervention handling
4. Add command-line flags for mode selection

**Implementation**:
```python
# cli/main.py
from agents.core.router import ExecutionRouter
from agents.core.standalone import StandaloneAgent
from agents.tools.builtin.delegate import delegate
from cli.display import SubAgentDisplay

def main():
    display = SubAgentDisplay()
    router = ExecutionRouter()

    # Get user task
    task = input("Task: ")

    # Calculate complexity
    complexity = router.calculate_complexity(task)

    if router.should_delegate(task, complexity):
        print(f"🔀 Complexity: {complexity:.2f} - Using sub-agent mode")

        # Determine best role
        role = determine_role(task)  # Helper function

        # Show sub-agent execution
        from threading import Thread

        output_stream = Queue()
        user_input_queue = Queue()

        # Start display in separate thread
        display_thread = Thread(
            target=display.show_execution_stream,
            args=(f"subagent_{role}", output_stream, role)
        )
        display_thread.start()

        # Start user input monitoring
        def monitor_user_input():
            while True:
                feedback = display.prompt_for_intervention()
                if feedback:
                    user_input_queue.put({
                        "timestamp": datetime.now(),
                        "instruction": feedback,
                        "type": "course_correction"
                    })

        input_thread = Thread(target=monitor_user_input)
        input_thread.daemon = True
        input_thread.start()

        # Execute delegation
        result = delegate(task, role, stream_to_user=True)

        # Wait for display to finish
        output_stream.put({"type": "completion"})
        display_thread.join()

        # Show final result
        print(f"\n✅ Task completed: {result['summary']}")
    else:
        print(f"⚡ Complexity: {complexity:.2f} - Using standalone mode")
        standalone = StandaloneAgent()
        result = standalone.execute(task, role="generalist")
        print(f"\n✅ {result}")
```

### Phase 4: Testing & Refinement (Week 6)

#### Step 8: Integration Testing
**Priority**: Critical
**Estimated Time**: 5 days

**Test Scenarios**:
1. **Standalone Mode Tests**:
   - Simple file edits
   - Single queries
   - Quick fixes

2. **Sub-agent Mode Tests**:
   - Complex multi-file tasks
   - User intervention during execution
   - Multiple user interventions
   - Error recovery

3. **Edge Cases**:
   - Empty user input
   - Rapid interventions
   - Network/API failures
   - Invalid roles

**Testing Framework**:
```python
# tests/test_subagent_system.py
import pytest
from agents.core.router import ExecutionRouter
from agents.core.standalone import StandaloneAgent
from agents.tools.builtin.delegate import delegate

class TestExecutionRouter:
    def test_simple_task_standalone(self):
        router = ExecutionRouter()
        task = "Fix typo in README.md"
        complexity = router.calculate_complexity(task)
        assert complexity < 0.3
        assert not router.should_delegate(task, complexity)

    def test_complex_task_delegation(self):
        router = ExecutionRouter()
        task = "Build authentication system with JWT, refresh tokens, and role-based access control"
        complexity = router.calculate_complexity(task)
        assert complexity > 0.3
        assert router.should_delegate(task, complexity)

class TestStandaloneAgent:
    def test_simple_execution(self):
        agent = StandaloneAgent()
        result = agent.execute("Echo hello world", role="generalist")
        assert result is not None

class TestDelegateSystem:
    def test_delegation_with_backend_role(self):
        result = delegate(
            task="Create a simple REST API endpoint",
            role="backend_developer",
            stream_to_user=False
        )
        assert result["status"] in ["completed", "failed"]
        assert "summary" in result

    def test_user_intervention(self):
        # Test with simulated user input
        # This requires mocking the queue system
        pass
```

#### Step 9: Documentation
**Priority**: Medium
**Estimated Time**: 2 days

**Documents to Create**:
1. **User Guide**: How to use standalone vs sub-agent modes
2. **Developer Guide**: How to add new roles and customize behavior
3. **API Reference**: All classes, methods, and their parameters
4. **Architecture Diagram**: Visual representation of system flow

## 4. Safety and Constraints

### 4.1 Recursive Depth Control
**Problem**: Sub-agents spawning more sub-agents leads to infinite loops

**Solution**:
```python
# Add depth parameter to delegate
def delegate(task: str, role: str, stream_to_user: bool = True, depth: int = 0) -> dict:
    MAX_DEPTH = 1  # Sub-agents cannot spawn more sub-agents

    if depth >= MAX_DEPTH:
        raise RuntimeError(f"Maximum delegation depth ({MAX_DEPTH}) exceeded")

    # Pass depth to sub-agent
    agent = Agent(
        session_id=session_id,
        system_prompt=system_prompt,
        enable_streaming=stream_to_user,
        delegation_depth=depth + 1  # Increment depth
    )
```

### 4.2 Resource Management
**Considerations**:
- **Memory**: Each sub-agent has its own conversation history (limit to 50 messages)
- **Token Usage**: Monitor total tokens across all sub-agents (set budget limits)
- **File Operations**: All agents share file system (use file locking)

**Implementation**:
```python
class Agent:
    MAX_HISTORY_LENGTH = 50
    TOKEN_BUDGET = 100000

    def _add_to_history(self, message: dict):
        self.conversation_history.append(message)

        # Trim history if too long
        if len(self.conversation_history) > self.MAX_HISTORY_LENGTH:
            # Keep system prompt + last 40 messages
            self.conversation_history = [
                self.conversation_history[0],  # System prompt
                *self.conversation_history[-40:]
            ]

        # Check token budget
        total_tokens = sum(estimate_tokens(msg["content"]) for msg in self.conversation_history)
        if total_tokens > self.TOKEN_BUDGET:
            raise RuntimeError("Token budget exceeded")
```

### 4.3 Error Handling & Recovery
**Strategies**:
1. **Graceful Degradation**: If sub-agent fails, fallback to planner handling
2. **Partial Results**: Return partial work even if not fully complete
3. **User Notification**: Always inform user of failures with actionable info

**Implementation**:
```python
try:
    result = delegate(task, role)
except Exception as e:
    logger.error(f"Sub-agent failed: {e}")
    # Fallback to planner
    result = planner.handle_task_directly(task)
    print(f"⚠️  Sub-agent failed, planner handling directly: {e}")
```

### 4.4 Termination Conditions
Sub-agents must stop when:
1. **Explicit Completion**: Agent states task is done
2. **Token Limit**: Approaching token budget
3. **Time Limit**: Exceeded maximum execution time (configurable)
4. **User Termination**: User sends stop signal
5. **Error Threshold**: Too many consecutive errors

```python
class Agent:
    MAX_EXECUTION_TIME = 600  # 10 minutes
    MAX_CONSECUTIVE_ERRORS = 3

    def _should_terminate(self) -> bool:
        return (
            self._is_task_complete() or
            self._token_budget_exceeded() or
            self._time_limit_exceeded() or
            self._user_requested_stop() or
            self._too_many_errors()
        )
```

## 5. Future Enhancements

### 5.1 Multi-Agent Coordination
Allow planner to coordinate multiple sub-agents working in parallel on different sub-tasks

### 5.2 Agent Learning
Sub-agents learn from successful patterns and improve over time

### 5.3 Advanced Role System
Dynamic role generation based on task analysis rather than predefined roles

### 5.4 Collaborative Editing
Multiple sub-agents can work on same files with conflict resolution

## 6. Glossary

**Planner**: Main coordinating agent that creates PROJECT_PLAN.md and delegates tasks
**Sub-agent**: Specialized worker agent that executes specific delegated tasks
**Standalone Mode**: Direct execution without planning/delegation overhead
**Role**: Specialized agent configuration (backend_developer, frontend_engineer, etc.)
**Streaming**: Real-time display of agent thoughts and actions
**User Intervention**: Mid-execution user feedback to steer agent direction
**Execution Router**: Decision system that chooses standalone vs sub-agent mode
**Complexity Score**: 0.0-1.0 metric indicating task complexity for routing decisions
