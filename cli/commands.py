import sys
from agents.core.agent import Agent

class CLI:
    def __init__(self):
        self.agent = Agent()
        self.running = True

    def _print_welcome(self):
        """Display welcome message"""
        print("=" * 60)
        print("Welcome to Entourage AI Assistant")
        print("=" * 60)
        print("Commands:")
        print("  /help    - Show this help message")
        print("  /clear   - Clear conversation history")
        print("  /history - Show conversation history")
        print("  /exit    - Exit the application")
        print("=" * 60)
        print()

    def _print_help(self):
        """Display help message"""
        print("\nAvailable commands:")
        print("  /help    - Show this help message")
        print("  /clear   - Clear conversation history")
        print("  /history - Show conversation history")
        print("  /exit    - Exit the application")
        print()

    def _clear_history(self):
        """Clear conversation history"""
        self.agent = Agent()
        print("\n✓ Conversation history cleared.\n")

    def _show_history(self):
        """Display conversation history"""
        history = self.agent.get_conversation_history()
        print("\n" + "=" * 60)
        print("Conversation History")
        print("=" * 60)
        for msg in history:
            role = msg.get('role', 'unknown').upper()
            content = msg.get('content', '')
            print(f"\n[{role}]:")
            print(content)
        print("=" * 60 + "\n")

    def _handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if command was handled."""
        if not user_input.startswith('/'):
            return False

        command = user_input.lower().strip()

        if command == '/exit':
            self.running = False
            print("\nGoodbye! 👋\n")
            return True
        elif command == '/help':
            self._print_help()
            return True
        elif command == '/clear':
            self._clear_history()
            return True
        elif command == '/history':
            self._show_history()
            return True
        else:
            print(f"\n⚠️  Unknown command: {command}")
            print("Type /help for available commands.\n")
            return True

    def _process_user_input(self, user_input: str):
        """Process user input and stream response"""
        try:
            response = self.agent.process_message(user_input, stream=True)
            print("\nAssistant: ", end="", flush=True)

            for chunk in response:
                print(chunk, flush=True, end="")

            print("\n")  # Add newline after response

        except KeyboardInterrupt:
            print("\n\n⚠️  Response interrupted by user.\n")
        except Exception as e:
            print(f"\n\n❌ Error processing message: {str(e)}\n")

    def run(self):
        """Main CLI loop"""
        self._print_welcome()

        try:
            while self.running:
                try:
                    user_input = input("You: ").strip()

                    # Skip empty input
                    if not user_input:
                        continue

                    # Handle commands
                    if self._handle_command(user_input):
                        continue

                    # Process regular message
                    self._process_user_input(user_input)

                except KeyboardInterrupt:
                    print("\n\nUse /exit to quit or continue chatting.\n")
                    continue
                except EOFError:
                    # Handle Ctrl+D
                    self.running = False
                    print("\n\nGoodbye! 👋\n")
                    break

        except Exception as e:
            print(f"\n\n❌ Fatal error: {str(e)}\n")
            sys.exit(1)

        sys.exit(0)
