# Setup Guide (Hinglish)

## Step 1: GitHub repo banao
1. GitHub.com pe login karo (username: ap5487060-crypto)
2. Naya repo banao, naam do: `telegram-banner-bot`
3. Is folder ke saare files (post_banner.py, requirements.txt, .github/workflows/post_banner.yml) us repo mein upload karo
   - Sabse aasan tarika: GitHub website pe "Add file -> Upload files" se saari files drag-drop kar do
   - Dhyan rakho: `.github/workflows/post_banner.yml` ka folder structure bhi waisa hi rehna chahiye

## Step 2: GitHub Secrets add karo
Repo ke andar: **Settings -> Secrets and variables -> Actions -> New repository secret**

Ye 6 secrets banao (naam bilkul same rakhna):

| Secret Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Tumhara BotFather se mila token |
| `TELEGRAM_CHANNEL` | `@MISSION_SSC_CGL1` |
| `GROQ_API_KEY` | Tumhara Groq API key |
| `GDRIVE_NEW_FOLDER_ID` | `17ySpUIM1pC5w4g2Uv0YDeNZc1wtfChYR` |
| `GDRIVE_POSTED_FOLDER_ID` | `1lfqX0SdMfgeRSZ1Owe7Q67hDVrVkzFw2` |
| `GDRIVE_SERVICE_ACCOUNT_JSON` | Downloaded JSON file ka **poora content** copy-paste kar do (pura `{...}` object) |

## Step 3: Test karo
1. Repo mein **Actions** tab pe jao
2. "Auto Post Banner to Telegram" workflow select karo
3. **Run workflow** button dabao (manual trigger)
4. Logs check karo — agar sab sahi hai to tumhare Telegram channel pe photo + caption aa jayega

## Step 4: Daily automatic
Workflow already set hai roz **subah 8:30 AM IST** chalne ke liye (`.github/workflows/post_banner.yml` mein cron line). Jab bhi tum Drive ke `new_banners` folder mein photo daaloge, agle scheduled run mein wo automatically post ho jayegi aur `posted` folder mein move ho jayegi.

Time change karna ho to `cron: "0 3 * * *"` line edit karo (format: minute hour day month weekday, UTC time mein — IST = UTC + 5:30).

## Common issues
- **Workflow fail ho raha hai / "KeyError"** → koi secret ka naam galat type hua hai, dobara check karo
- **Telegram pe post nahi ho raha** → Bot channel mein Admin hai ya nahi check karo
- **Drive access error** → service account email ko dono folder (`new_banners`, `posted`) mein Editor access diya hai ya nahi check karo
- **Groq model error** → Groq apna model list kabhi kabhi badalta hai; agar `qwen/qwen3.6-27b` fail ho to console.groq.com pe jaake current vision model ka naam check karke `post_banner.py` mein `GROQ_VISION_MODEL` line update karo
