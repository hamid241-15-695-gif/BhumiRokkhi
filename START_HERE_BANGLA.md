# ভূমিরক্ষী — সহজ ২-ফাইল দলিল যাচাই

## V4-এর নতুন আপডেট চালু করো

১. বর্তমানে চলা V4-এর VS Code Terminal-এ:

```powershell
docker compose down
```

২. `BhumiRokkhi_V4_Updated.zip` ডাউনলোড করে **Extract All** করো। আগের V4 ফোল্ডার Delete করবে না। Extract করা **BhumiRokkhi_V4** ফোল্ডারটি VS Code-এ Open করো।

৩. Docker Desktop চালু রেখে নতুন ফোল্ডারের Terminal-এ:

```powershell
docker compose up --build -d
```

৪. Browser-এ যাও: **http://localhost:3000/check**। Login অথবা Guest দিয়ে প্রবেশ করো।

**আগের V4 Account মুছবে না** — কারণ Docker Compose project name ও volume আগের মতোই আছে। `docker compose down -v` **দেবে না**।

## নিজের দলিল যাচাই — শুধু ২টি Upload

১. নিচের **নিজের নমুনা দলিল যাচাই** অংশে যাও।

২. **নিজের নমুনা দলিল নির্বাচন করুন** → `D-4001_reference.pdf` (বা তোমার অনুমোদিত কাল্পনিক PDF) আপলোড করো।

৩. **এই ফাইলটি আমার নিজের বা অনুমোদিত নমুনা** চেকবক্সে টিক দিয়ে **নমুনা দলিল সংরক্ষণ করুন** চাপো।

৪. নিচে **যে দলিল যাচাই করবেন** → **একই PDF** আবার নির্বাচন করো → **দলিল যাচাই করুন** → **হুবহু একই ফাইল**।

৫. একই স্থানে `D-4001_changed_version.pdf` আপলোড করে যাচাই করো → **ফাইলের হ্যাশ আলাদা**।

৬. নতুন নমুনা সংরক্ষণ করলে আগের নমুনা বদলে যাবে। আবার যাচাই করলে সবসময় নতুন সংরক্ষিত নমুনাটির সঙ্গে তুলনা হবে।

**এখানে আর Reference Name, Code অথবা Dropdown নেই।** অন্য সব আগের মতো থাকবে।

### কেন এটি সরকারি সত্যায়ন নয়?

একই Hash মানে দুটি ফাইলের bytes হুবহু একই। Hash আলাদা মানে ফাইলের bytes আলাদা। কোনো ফলাফলই দলিলের আইনগত সত্যতা বা জালিয়াতি নিশ্চিত করে না।

### ON/OFF

- `docker compose up -d` — চালু
- `docker compose down` — বন্ধ
- `docker compose logs --tail=80` — Error দেখো

Docker Desktop চালু থাকতে হবে। Demo OTP `1234` শুধু পরীক্ষার জন্য।
