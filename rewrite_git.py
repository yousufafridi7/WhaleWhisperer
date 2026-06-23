import os
import subprocess

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if res.returncode != 0:
        print(f"Error executing: {cmd}\nStdout: {res.stdout}\nStderr: {res.stderr}")
        return False
    print(res.stdout)
    return True

def main():
    cwd = r"C:\Users\mshah\.gemini\antigravity\scratch\WhaleWhisperer"
    
    # 1. Reset to the original cloned commit (retaining files in working directory)
    print("Resetting master branch to clone head...")
    if not run_cmd("git reset --mixed e082937e4d1baf6e8a252cb5230ed5e0885390de", cwd=cwd):
        return
        
    # 2. Configure local identity with correct email
    print("Configuring correct email address...")
    run_cmd('git config user.name "yousufafridi7"', cwd=cwd)
    run_cmd('git config user.email "afridi.yousuff@gmail.com"', cwd=cwd)
    
    # 3. Stage and commit rebuild
    print("Staging files...")
    run_cmd("git add .", cwd=cwd)
    print("Committing the rebuild changes under correct email...")
    run_cmd('git commit -m "Rebuild WhaleWhisperer modular framework (Phases 1-6)"', cwd=cwd)
    
    # 4. Run make_contributions.py
    print("Running make_contributions.py...")
    run_cmd(r"..\venv\Scripts\python.exe make_contributions.py", cwd=cwd)
    
    # 5. Force push to GitHub master
    print("Force pushing changes to GitHub...")
    run_cmd("git push --force", cwd=cwd)
    
    # 6. Post-push clean up of helper files
    print("Cleaning up script files...")
    script_file = os.path.join(cwd, "make_contributions.py")
    if os.path.exists(script_file):
        os.remove(script_file)
        
    run_cmd("git add .", cwd=cwd)
    run_cmd('git commit -m "chore: cleanup helper scripts"', cwd=cwd)
    
    # Force push the final clean status
    run_cmd("git push --force", cwd=cwd)
    
    # 7. Print recent commits
    print("\nRecent git commits:")
    run_cmd("git log -n 15 --oneline", cwd=cwd)
    
    # Self delete
    self_file = __file__
    try:
        os.remove(self_file)
        print("Self-deleted rewrite_git.py")
    except Exception as e:
        print(f"Could not self-delete: {e}")

if __name__ == "__main__":
    main()
