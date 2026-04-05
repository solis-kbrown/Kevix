"""
ServerRoot.net - LOLBin Execution Module
Execute commands using only legitimate Windows system tools
"""

import subprocess
import json
import base64
import os
import time
from typing import Dict, List, Optional, Tuple
import threading


class LOLBinExecutor:
    """
    Execute commands using Living Off The Land Binaries
    Only uses signed Microsoft tools - no custom executables
    """
    
    # Available LOLBins (all signed by Microsoft)
    LOLBINS = {
        'powershell': {
            'path': 'powershell.exe',
            'description': 'PowerShell - automation framework',
            'signed': True,
            'capabilities': ['execution', 'download', 'process_injection']
        },
        'wmic': {
            'path': 'wmic.exe',
            'description': 'Windows Management Instrumentation Commandline',
            'signed': True,
            'capabilities': ['system_info', 'process_management', 'service_management']
        },
        'cmd': {
            'path': 'cmd.exe',
            'description': 'Command Prompt',
            'signed': True,
            'capabilities': ['basic_commands', 'file_operations']
        },
        'reg': {
            'path': 'reg.exe',
            'description': 'Windows Registry Editor',
            'signed': True,
            'capabilities': ['registry_operations']
        },
        'schtasks': {
            'path': 'schtasks.exe',
            'description': 'Task Scheduler',
            'signed': True,
            'capabilities': ['scheduled_tasks', 'persistence']
        },
        'wscript': {
            'path': 'wscript.exe',
            'description': 'Windows Script Host',
            'signed': True,
            'capabilities': ['script_execution']
        },
        'cscript': {
            'path': 'cscript.exe',
            'description': 'Console Script Host',
            'signed': True,
            'capabilities': ['script_execution']
        },
        'rundll32': {
            'path': 'rundll32.exe',
            'description': 'Run DLL',
            'signed': True,
            'capabilities': ['dll_execution', 'com_calls']
        },
        'regsvr32': {
            'path': 'regsvr32.exe',
            'description': 'Register Server',
            'signed': True,
            'capabilities': ['dll_loading', 'com_registration']
        },
        'mshta': {
            'path': 'mshta.exe',
            'description': 'HTML Application',
            'signed': True,
            'capabilities': ['html_execution', 'javascript']
        },
        'bitsadmin': {
            'path': 'bitsadmin.exe',
            'description': 'Background Intelligent Transfer Service',
            'signed': True,
            'capabilities': ['file_download', 'file_upload']
        },
        'certutil': {
            'path': 'certutil.exe',
            'description': 'Certificate Utility',
            'signed': True,
            'capabilities': ['file_operations', 'encoding', 'certificates']
        },
        'msiexec': {
            'path': 'msiexec.exe',
            'description': 'Windows Installer',
            'signed': True,
            'capabilities': ['package_installation', 'script_execution']
        },
        'findstr': {
            'path': 'findstr.exe',
            'description': 'Find String',
            'signed': True,
            'capabilities': ['text_search', 'file_search']
        },
        'tasklist': {
            'path': 'tasklist.exe',
            'description': 'Task List',
            'signed': True,
            'capabilities': ['process_listing']
        },
        'taskkill': {
            'path': 'taskkill.exe',
            'description': 'Task Kill',
            'signed': True,
            'capabilities': ['process_termination']
        },
        'net': {
            'path': 'net.exe',
            'description': 'Network Commands',
            'signed': True,
            'capabilities': ['user_management', 'share_management', 'services']
        },
        'sc': {
            'path': 'sc.exe',
            'description': 'Service Control',
            'signed': True,
            'capabilities': ['service_management']
        }
    }
    
    def __init__(self):
        self.execution_history = []
        self.session_id = self.generate_session_id()
    
    @staticmethod
    def generate_session_id() -> str:
        import uuid
        return str(uuid.uuid4())
    
    def execute(self, lolbin: str, command: List[str], 
                timeout: int = 30, 
                capture_output: bool = True) -> Tuple[bool, str, str]:
        try:
            if lolbin not in self.LOLBINS:
                return False, '', f"Unknown LOLBin: {lolbin}"
            
            lolbin_info = self.LOLBINS[lolbin]
            lolbin_path = lolbin_info['path']
            full_command = [lolbin_path] + command
            
            result = subprocess.run(
                full_command,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                shell=False
            )
            
            success = result.returncode == 0
            self.log_execution(lolbin, command, success)
            
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, '', 'Command timeout'
        except Exception as e:
            return False, '', f'Execution error: {str(e)}'
    
    def execute_powershell(self, script: str, 
                          encoded: bool = False,
                          bypass_policy: bool = True) -> Tuple[bool, str, str]:
        command = []
        
        if bypass_policy:
            command.extend(['-ExecutionPolicy', 'Bypass'])
        
        command.extend(['-NoProfile', '-NonInteractive'])
        
        if encoded:
            command.extend(['-EncodedCommand', script])
        else:
            command.extend(['-Command', script])
        
        return self.execute('powershell', command)
    
    def execute_wmic(self, query: str) -> Tuple[bool, str, str]:
        command = [query]
        return self.execute('wmic', command)
    
    def execute_registry(self, operation: str, 
                        key_path: str,
                        value_name: Optional[str] = None,
                        value_data: Optional[str] = None) -> Tuple[bool, str, str]:
        command = []
        
        if operation == 'add' or operation == 'delete' or operation == 'set':
            command.extend([operation, key_path])
            if value_name:
                command.extend(['/v', value_name])
            if value_data:
                command.extend(['/d', value_data])
            command.extend(['/f'])
        
        elif operation == 'query':
            command.extend(['query', key_path])
            if value_name:
                command.extend(['/v', value_name])
        
        return self.execute('reg', command)
    
    def execute_scheduled_task(self, operation: str,
                               task_name: str,
                               task_command: Optional[str] = None,
                               schedule: Optional[str] = None) -> Tuple[bool, str, str]:
        command = [operation]
        
        if operation == 'create':
            command.extend(['/tn', task_name, '/tr', task_command, '/sc', schedule, '/f'])
        elif operation == 'delete':
            command.extend(['/tn', task_name, '/f'])
        elif operation == 'query':
            command.extend(['/tn', task_name])
        elif operation == 'run':
            command.extend(['/tn', task_name])
        
        return self.execute('schtasks', command)
    
    def execute_network(self, command: str, args: List[str]) -> Tuple[bool, str, str]:
        full_args = [command] + args
        return self.execute('net', full_args)
    
    def execute_service(self, operation: str, 
                       service_name: str) -> Tuple[bool, str, str]:
        command = [operation, service_name]
        return self.execute('sc', command)
    
    def execute_file_download(self, url: str, 
                             destination: str) -> Tuple[bool, str, str]:
        job_name = f"Download_{self.session_id.replace('-', '_')}"
        
        create_cmd = ['transfer', 'download', job_name, url, destination]
        success, output, error = self.execute('bitsadmin', create_cmd)
        
        if not success:
            return False, '', f"Failed to create download job: {error}"
        
        start_cmd = ['transfer', job_name]
        success, output, error = self.execute('bitsadmin', start_cmd)
        
        self.execute('bitsadmin', ['delete', job_name])
        
        return success, output, error
    
    def execute_certutil_decode(self, input_file: str, 
                               output_file: str) -> Tuple[bool, str, str]:
        command = ['-decode', input_file, output_file]
        return self.execute('certutil', command)
    
    def execute_certutil_encode(self, input_file: str, 
                               output_file: str) -> Tuple[bool, str, str]:
        command = ['-encode', input_file, output_file]
        return self.execute('certutil', command)
    
    def log_execution(self, lolbin: str, command: List[str], success: bool):
        log_entry = {
            'timestamp': time.time(),
            'lolbin': lolbin,
            'command': ' '.join(command),
            'success': success,
            'session_id': self.session_id
        }
        
        self.execution_history.append(log_entry)
        
        if len(self.execution_history) > 100:
            self.execution_history.pop(0)
    
    def get_execution_stats(self) -> Dict:
        total = len(self.execution_history)
        successful = sum(1 for entry in self.execution_history if entry['success'])
        
        lolbin_usage = {}
        for entry in self.execution_history:
            lolbin = entry['lolbin']
            lolbin_usage[lolbin] = lolbin_usage.get(lolbin, 0) + 1
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': (successful / total) if total > 0 else 0,
            'lolbin_usage': lolbin_usage,
            'session_id': self.session_id
        }


def create_lolbin_executor() -> LOLBinExecutor:
    return LOLBinExecutor()


if __name__ == '__main__':
    executor = create_lolbin_executor()
    
    print("[LOLBinExecutor] Testing LOLBin execution...\n")
    
    print("[TEST 1] Listing processes using WMIC...")
    success, output, error = executor.execute_wmic('process get Name,ProcessId')
    print(f"Success: {success}")
    print(f"Output (first 200 chars): {output[:200]}\n")
    
    print("[TEST 2] Listing services using PowerShell...")
    ps_script = "Get-Service | Select-Object -First 5 Name, Status"
    success, output, error = executor.execute_powershell(ps_script)
    print(f"Success: {success}")
    print(f"Output (first 200 chars): {output[:200]}\n")
    
    print("[TEST 3] Querying registry...")
    success, output, error = executor.execute_registry('query', r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion')
    print(f"Success: {success}")
    print(f"Output (first 200 chars): {output[:200]}\n")
    
    print("[TEST 4] Execution statistics...")
    stats = executor.get_execution_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n[LOLBinExecutor] All tests completed!")