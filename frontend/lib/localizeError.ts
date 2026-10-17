import type {Lang} from '@/lib/i18n';
/** Translate known demo API errors; do not expose untranslated server text in Bangla mode. */
export function localizeError(error:unknown,lang:Lang):string {
  const message=error instanceof Error?error.message:String(error);
  if(lang==='en')return message;
  const lower=message.toLowerCase();
  if(lower.includes('account exists')||lower.includes('already exists'))return 'এই নম্বর দিয়ে আগে অ্যাকাউন্ট তৈরি করা হয়েছে। লগইন করো।';
  if(lower.includes('incorrect phone or password'))return 'ফোন নম্বর বা পাসওয়ার্ড সঠিক নয়।';
  if(lower.includes('demo otp'))return 'ডেমো ওটিপি 1234 ব্যবহার করো।';
  if(lower.includes('too many'))return 'অনেকবার চেষ্টা করা হয়েছে। একটু পরে আবার চেষ্টা করো।';
  if(lower.includes('maximum 8 mb'))return 'ফাইলের সর্বোচ্চ আকার ৮ এমবি।';
  if(lower.includes('supported:'))return 'শুধু পিডিএফ, পিএনজি বা জেপিজি ফাইল গ্রহণ করা হয়।';
  if(lower.includes('invalid session')||lower.includes('expired session'))return 'সেশনের মেয়াদ শেষ। আবার লগইন করো।';
  if(lower.includes('reference')&&lower.includes('not found'))return 'এই অ্যাকাউন্টে রেফারেন্স পাওয়া যায়নি।';
  if(lower.includes('already registered'))return 'এই রেফারেন্স কোড আগে ব্যবহার করা হয়েছে। নতুন কোড দাও।';
  if(lower.includes('failed to fetch')||lower.includes('networkerror'))return 'সার্ভারের সঙ্গে সংযোগ করা যায়নি। Docker চলছে কি না দেখো।';
  if(lower.includes('missing')||lower.includes('validation'))return 'দেওয়া তথ্য সম্পূর্ণ বা সঠিক নয়। আবার যাচাই করো।';
  return 'যাচাই বা সংযোগে সমস্যা হয়েছে। ইনপুট এবং সার্ভার পরীক্ষা করো।';
}
