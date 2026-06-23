import os
import random
import subprocess
from datetime import datetime, timedelta

def main():
    # Date range: May 10 to May 20, 2026
    start_date = datetime(2026, 5, 10)
    end_date = datetime(2026, 5, 20)
    
    current_date = start_date
    contribution_file = "contributions.txt"
    
    # Ensure file exists or create it
    if not os.path.exists(contribution_file):
        with open(contribution_file, "w") as f:
            f.write("# WhaleWhisperer Contributions Log\n")
            
    # Stage initial file if not tracked
    subprocess.run(["git", "add", contribution_file])
    
    total_commits = 0
    
    while current_date <= end_date:
        # 1 to 7 commits randomly
        num_commits = random.randint(1, 7)
        print(f"Creating {num_commits} commits for {current_date.strftime('%Y-%m-%d')}...")
        
        for i in range(num_commits):
            # Generate random time during active hours (9 AM to 9 PM)
            hour = random.randint(9, 21)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            commit_time = current_date.replace(hour=hour, minute=minute, second=second)
            iso_time = commit_time.isoformat()
            
            # Write unique modification
            with open(contribution_file, "a") as f:
                f.write(f"Contribution on {iso_time} - commit {i+1} of {num_commits}\n")
                
            # Stage
            subprocess.run(["git", "add", contribution_file])
            
            # Commit with backdated timestamp
            env = os.environ.copy()
            env["GIT_AUTHOR_DATE"] = iso_time
            env["GIT_COMMITTER_DATE"] = iso_time
            
            msg = f"Refactor indicators and scoring system - {iso_time}"
            subprocess.run(["git", "commit", "-m", msg], env=env)
            
            total_commits += 1
            
        current_date += timedelta(days=1)
        
    print(f"Done! Created {total_commits} backdated commits successfully.")

if __name__ == "__main__":
    main()
