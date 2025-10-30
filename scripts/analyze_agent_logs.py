"""
Agent Log Analysis Tool
Analyze agent_monitoring.log to identify patterns, issues, and performance metrics
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AgentLogAnalyzer:
    """Analyze agent monitoring logs"""
    
    def __init__(self, log_file: str = "agent_monitoring.log"):
        self.log_file = project_root / log_file
        self.events = []
        self.sessions = {}
        self.load_logs()
    
    def load_logs(self):
        """Load and parse log file"""
        if not self.log_file.exists():
            print(f"❌ Log file not found: {self.log_file}")
            print("Run some queries first to generate logs.")
            return
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    self.events.append(event)
                    
                    # Group by session
                    session_id = event.get('session_id')
                    if session_id:
                        if session_id not in self.sessions:
                            self.sessions[session_id] = []
                        self.sessions[session_id].append(event)
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ Loaded {len(self.events)} events from {len(self.sessions)} sessions")
    
    def analyze_performance(self):
        """Analyze performance metrics"""
        print("\n" + "="*70)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*70)
        
        session_ends = [e for e in self.events if e['event'] == 'session_end']
        
        if not session_ends:
            print("No completed sessions found.")
            return
        
        # Duration statistics
        durations = [e['data']['duration_seconds'] for e in session_ends]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        
        print(f"\n📈 Query Duration:")
        print(f"  Average: {avg_duration:.2f}s")
        print(f"  Min: {min_duration:.2f}s")
        print(f"  Max: {max_duration:.2f}s")
        
        # Success rate
        successful = sum(1 for e in session_ends if e['data']['status'] == 'completed')
        success_rate = (successful / len(session_ends)) * 100
        
        print(f"\n✅ Success Rate: {success_rate:.1f}% ({successful}/{len(session_ends)})")
        
        # Retry statistics
        retries = [e['data']['retries'] for e in session_ends]
        avg_retries = sum(retries) / len(retries)
        total_retries = sum(retries)
        
        print(f"\n🔄 Retry Statistics:")
        print(f"  Total retries: {total_retries}")
        print(f"  Average per query: {avg_retries:.2f}")
        print(f"  Queries with retries: {sum(1 for r in retries if r > 0)}/{len(retries)}")
        
        # Tool usage
        tool_calls = [e['data']['tool_calls'] for e in session_ends]
        avg_tool_calls = sum(tool_calls) / len(tool_calls)
        
        print(f"\n🔧 Tool Usage:")
        print(f"  Average tool calls per query: {avg_tool_calls:.2f}")
        
        # Sub-agent usage
        subagent_calls = [e['data']['subagent_calls'] for e in session_ends]
        avg_subagent = sum(subagent_calls) / len(subagent_calls)
        
        print(f"\n🤖 Sub-Agent Usage:")
        print(f"  Average sub-agent calls per query: {avg_subagent:.2f}")
    
    def analyze_errors(self):
        """Analyze common errors"""
        print("\n" + "="*70)
        print("🐛 ERROR ANALYSIS")
        print("="*70)
        
        query_attempts = [e for e in self.events if e['event'] == 'query_attempt']
        failed_attempts = [e for e in query_attempts if not e['data']['success']]
        
        if not failed_attempts:
            print("\n✅ No query failures found!")
            return
        
        print(f"\n❌ Total failed queries: {len(failed_attempts)}")
        
        # Error types
        error_types = Counter()
        for attempt in failed_attempts:
            error = attempt['data'].get('error', '')
            if 'datetime' in error.lower():
                error_types['datetime_functions'] += 1
            elif 'does not exist' in error.lower():
                error_types['missing_properties'] += 1
            elif 'contains' in error.lower():
                error_types['contains_syntax'] += 1
            elif 'syntax' in error.lower():
                error_types['cypher_syntax'] += 1
            else:
                error_types['other'] += 1
        
        print("\n📊 Error Types:")
        for error_type, count in error_types.most_common():
            print(f"  {error_type}: {count}")
        
        # Most common failing queries
        print("\n🔍 Sample Failed Queries:")
        for attempt in failed_attempts[:3]:
            cypher = attempt['data']['cypher']
            error = attempt['data']['error'][:100]
            print(f"\n  Query: {cypher}")
            print(f"  Error: {error}...")
    
    def analyze_sources(self):
        """Analyze query sources"""
        print("\n" + "="*70)
        print("📍 SOURCE ANALYSIS")
        print("="*70)
        
        session_starts = [e for e in self.events if e['event'] == 'session_start']
        
        if not session_starts:
            print("No sessions found.")
            return
        
        sources = Counter(e['data']['source'] for e in session_starts)
        
        print("\n📊 Queries by Source:")
        for source, count in sources.most_common():
            print(f"  {source}: {count}")
    
    def analyze_tool_performance(self):
        """Analyze tool execution performance"""
        print("\n" + "="*70)
        print("🔧 TOOL PERFORMANCE")
        print("="*70)
        
        tool_calls = [e for e in self.events if e['event'] == 'tool_call']
        
        if not tool_calls:
            print("No tool calls found.")
            return
        
        # Group by tool
        by_tool = defaultdict(list)
        for call in tool_calls:
            tool_name = call['data']['tool']
            by_tool[tool_name].append(call['data'])
        
        print("\n📊 Tool Statistics:")
        for tool_name, calls in by_tool.items():
            total = len(calls)
            successful = sum(1 for c in calls if c['success'])
            success_rate = (successful / total) * 100
            avg_duration = sum(c['duration_ms'] for c in calls) / total
            
            print(f"\n  {tool_name}:")
            print(f"    Calls: {total}")
            print(f"    Success rate: {success_rate:.1f}%")
            print(f"    Avg duration: {avg_duration:.0f}ms")
    
    def show_recent_sessions(self, limit: int = 5):
        """Show recent sessions"""
        print("\n" + "="*70)
        print(f"📜 RECENT SESSIONS (Last {limit})")
        print("="*70)
        
        session_ends = sorted(
            [e for e in self.events if e['event'] == 'session_end'],
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
        
        for i, session in enumerate(session_ends, 1):
            data = session['data']
            status_emoji = "✅" if data['status'] == 'completed' else "❌"
            
            print(f"\n{i}. {status_emoji} Session {data['session_id'][:8]}...")
            print(f"   Source: {data['source']}")
            print(f"   Duration: {data['duration_seconds']:.2f}s")
            print(f"   Retries: {data['retries']}")
            print(f"   Sub-agents: {data['subagent_calls']}")
            print(f"   Tool calls: {data['tool_calls']}")
            print(f"   Answer length: {data['answer_length']} chars")
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*70)
        print("🎯 AGENT MONITORING REPORT")
        print("="*70)
        print(f"Log file: {self.log_file}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.analyze_performance()
        self.analyze_errors()
        self.analyze_sources()
        self.analyze_tool_performance()
        self.show_recent_sessions()
        
        print("\n" + "="*70)
        print("✅ Analysis complete!")
        print("="*70)


def main():
    """Main function"""
    analyzer = AgentLogAnalyzer()
    
    if not analyzer.events:
        print("\n💡 Tip: Run some queries in the admin panel or WhatsApp to generate logs.")
        return
    
    analyzer.generate_report()


if __name__ == '__main__':
    main()

