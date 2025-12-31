import asyncio
import json
import tempfile
import os
import subprocess
from typing import Dict, Any

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

class CodeSandbox:
    """Secure code execution in Docker containers (or fallback to subprocess)"""
    
    def __init__(self):
        self.timeout = 5  # seconds
        self.docker_available = False
        
        if DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                self.client.ping()
                self.docker_available = True
                print("✅ Docker available - using sandboxed execution")
            except Exception as e:
                print(f"⚠️  Docker not available: {e}")
                print("ℹ️  Using fallback mode (limited security)")
                self.docker_available = False
        else:
            print("⚠️  Docker not installed - using fallback mode")
            self.docker_available = False
        
    async def execute_code(self, code: str, language: str) -> Dict[str, Any]:
        """Execute code in sandboxed environment or fallback"""
        try:
            if language == "python":
                if self.docker_available:
                    return await self._execute_python_docker(code)
                else:
                    return await self._execute_python_subprocess(code)
            elif language == "javascript":
                if self.docker_available:
                    return await self._execute_javascript_docker(code)
                else:
                    return await self._execute_javascript_subprocess(code)
            else:
                return {"error": "Unsupported language", "output": ""}
        except Exception as e:
            return {"error": str(e), "output": ""}
    
    async def _execute_python_subprocess(self, code: str) -> Dict[str, Any]:
        """Execute Python using subprocess (DEMO MODE - NOT SECURE)"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Run with timeout
            try:
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    return {
                        "output": result.stdout,
                        "error": None,
                        "executed_successfully": True,
                        "mode": "subprocess"
                    }
                else:
                    return {
                        "output": result.stdout,
                        "error": result.stderr or self._parse_python_error(result.stderr),
                        "executed_successfully": False,
                        "line": self._extract_error_line(result.stderr),
                        "mode": "subprocess"
                    }
            except subprocess.TimeoutExpired:
                os.unlink(temp_file)
                return {
                    "error": "Execution timeout (5s limit)",
                    "output": "",
                    "executed_successfully": False,
                    "mode": "subprocess"
                }
                
        except Exception as e:
            return {
                "error": f"Execution error: {str(e)}",
                "output": "",
                "executed_successfully": False,
                "mode": "subprocess"
            }
    
    async def _execute_javascript_subprocess(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript using subprocess (DEMO MODE)"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                os.unlink(temp_file)
                
                return {
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                    "executed_successfully": result.returncode == 0,
                    "mode": "subprocess"
                }
            except subprocess.TimeoutExpired:
                os.unlink(temp_file)
                return {
                    "error": "Execution timeout",
                    "output": "",
                    "executed_successfully": False,
                    "mode": "subprocess"
                }
            except FileNotFoundError:
                return {
                    "error": "Node.js not installed",
                    "output": "",
                    "executed_successfully": False,
                    "mode": "subprocess"
                }
                
        except Exception as e:
            return {
                "error": f"Execution error: {str(e)}",
                "output": "",
                "executed_successfully": False,
                "mode": "subprocess"
            }
    
    async def _execute_python_docker(self, code: str) -> Dict[str, Any]:
        """Execute Python code in Docker"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            container = self.client.containers.run(
                "python:3.11-slim",
                f"python {os.path.basename(temp_file)}",
                volumes={os.path.dirname(temp_file): {'bind': '/app', 'mode': 'ro'}},
                working_dir='/app',
                detach=True,
                mem_limit='128m',
                cpu_quota=50000,
                network_disabled=True,
                remove=True
            )
            
            try:
                result = container.wait(timeout=self.timeout)
                logs = container.logs().decode('utf-8')
                
                os.unlink(temp_file)
                
                if result['StatusCode'] == 0:
                    return {
                        "output": logs,
                        "error": None,
                        "executed_successfully": True,
                        "mode": "docker"
                    }
                else:
                    return {
                        "output": logs,
                        "error": self._parse_python_error(logs),
                        "executed_successfully": False,
                        "line": self._extract_error_line(logs),
                        "mode": "docker"
                    }
            except:
                container.stop()
                return {
                    "error": "Execution timeout (5s limit)",
                    "output": "",
                    "executed_successfully": False,
                    "mode": "docker"
                }
                
        except Exception as e:
            return {
                "error": f"Docker error: {str(e)}",
                "output": "",
                "executed_successfully": False,
                "mode": "docker"
            }
    
    async def _execute_javascript_docker(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code in Docker"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            container = self.client.containers.run(
                "node:18-slim",
                f"node {os.path.basename(temp_file)}",
                volumes={os.path.dirname(temp_file): {'bind': '/app', 'mode': 'ro'}},
                working_dir='/app',
                detach=True,
                mem_limit='128m',
                cpu_quota=50000,
                network_disabled=True,
                remove=True
            )
            
            try:
                result = container.wait(timeout=self.timeout)
                logs = container.logs().decode('utf-8')
                
                os.unlink(temp_file)
                
                return {
                    "output": logs,
                    "error": logs if result['StatusCode'] != 0 else None,
                    "executed_successfully": result['StatusCode'] == 0,
                    "mode": "docker"
                }
            except:
                container.stop()
                return {
                    "error": "Execution timeout",
                    "output": "",
                    "executed_successfully": False,
                    "mode": "docker"
                }
                
        except Exception as e:
            return {
                "error": f"Docker error: {str(e)}",
                "output": "",
                "executed_successfully": False,
                "mode": "docker"
            }
    
    def _parse_python_error(self, logs: str) -> str:
        """Extract meaningful error from Python traceback"""
        if not logs:
            return "Unknown error"
        lines = logs.strip().split('\n')
        if lines:
            return lines[-1]
        return "Unknown error"
    
    def _extract_error_line(self, logs: str) -> int:
        """Extract line number from error"""
        if not logs:
            return None
        import re
        match = re.search(r'line (\d+)', logs)
        if match:
            return int(match.group(1))
        return None
    
    def is_healthy(self) -> bool:
        """Check if execution environment is available"""
        return True  # Always return True since we have fallback
