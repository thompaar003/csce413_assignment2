import paramiko
import time

def attack():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Connecting to honeypot...")
    try:
        client.connect('localhost', port=2222, username='root', password='password123')
        print("Connected!")
        
        shell = client.invoke_shell()
        # Wait for banner
        time.sleep(1)
        while shell.recv_ready():
            print(f"Banner: {shell.recv(1024).decode()}")

        commands = ['ls', 'pwd', 'whoami', 'id', 'cat /etc/passwd', 'exit']
        
        for cmd in commands:
            print(f"Sending: {cmd}")
            shell.send(cmd + '\n')
            time.sleep(1)
            while shell.recv_ready():
                output = shell.recv(4096).decode()
                print(f"Output: {output}")
            
    except Exception as e:
        print(f"Attack failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    attack()
