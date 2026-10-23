# Rollar va ruxsatlar matritsasi

Har yuqori rol pastdagilarning barcha huquqlarini o‘z ichiga oladi (`user.has_role_at_least(Role.X)`).
Koddagi identifikatorlar: `Role.USER=1`, `Role.JURY=2`, `Role.JURY_PRO=3`, `Role.MODERATOR=4`, `Role.SUPERADMIN=5`.
Faol bo‘lmagan (`is_active=False`) foydalanuvchida hech qanday rol huquqi yo‘q. Django `is_superuser` — super admin darajasi.

Belgilar: ✅ — ruxsat; 👤 — faqat o‘ziniki; ⏱ — shart bilan (izohga qarang); — — yo‘q.

| Amal | Anonim | User | Jury | Jury Pro | Moderator | Super admin |
|---|---|---|---|---|---|---|
| Bosh sahifa, kurs, darslar, nashr etilgan vazifalar, reyting | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ro‘yxatdan o‘tish (yoqilgan bo‘lsa) | ✅ | | | | | |
| Yechim yuborish, quiz, loyiha topshirish | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| O‘z urinishlari va kodi | — | 👤 | 👤 | 👤 | ✅ | ✅ |
| Boshqaning kodi | — | ⏱¹ | ⏱¹ | ⏱¹ | ✅ | ✅ |
| Boshqaning profili (email/kontaktlarsiz) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rol so‘rash (Jury / Jury Pro) | — | ✅ | ✅ (Jury Pro) | — | — | — |
| Kontest yaratish va boshqarish | — | — | 👤 | 👤 | ✅ (hammasi) | ✅ |
| Reytingli kontest belgilash | — | — | — | — | ✅ | ✅ |
| Masala va test qo‘shish, etalon bilan tekshirish | — | — | — | 👤 | — ² | ✅ |
| Qoralama vazifa, yopiq testlar, etalon yechimni ko‘rish | — | — | — | 👤 | ✅ | ✅ |
| Vazifani nashr etish / ko‘rib chiqishga qaytarish | — | — | — | yuborish 👤 | ✅ | ✅ |
| Guruhlar, a’zolar, davomat, progress, baholar, CSV | — | — | — | — | ✅ | ✅ |
| Loyihalarni rubrika bo‘yicha baholash | — | — | — | — | ✅ | ✅ |
| Barcha yechimlar oqimi, qayta tekshirish | — | — | — | — | ✅ | ✅ |
| Ko‘chirmachilik natijalari | — | — | — | — | ✅ | ✅ |
| Rol so‘rovlarini tasdiqlash | — | — | — | — | ✅ | ✅ |
| Rol berish | — | — | — | — | user/jury/jury_pro ³ | barcha rollar |
| Vaqtinchalik parol berish | — | — | — | — | ⏱³ | ✅ |
| Admin panel (Django) | — | — | — | — | ✅ (cheklangan) | ✅ (2FA bilan) |
| Kurs tuzilmasini o‘zgartirish | — | — | — | — | ko‘rish | ✅ |
| Tizim sozlamalari, dizayn ranglari, ro‘yxatdan o‘tish | — | — | — | — | — | ✅ (2FA) |
| Audit jurnali, tizim holati | — | — | — | — | — | ✅ (2FA) |
| Foydalanuvchini o‘chirish | — | — | — | — | — | ✅ |
| Foydalanuvchi parolini **ko‘rish** | — | — | — | — | — | — (hech kim) |

¹ Faqat o‘zi shu masalani yechgan bo‘lsa yoki yechim tugagan kontestga tegishli bo‘lsa.
² Moderator boshqalarning vazifasini tahrirlamaydi, faqat ko‘radi va holatini o‘zgartiradi.
³ Faqat o‘zidan past darajadagi foydalanuvchiga; o‘ziga emas.

## Qayerda tekshiriladi

| Qatlam | Vosita |
|---|---|
| View (funksiya) | `accounts.permissions.role_required(Role.X)` |
| View (klass) | `accounts.permissions.RoleRequiredMixin` |
| Admin | `accounts.permissions.RoleAdminMixin` (`admin_role`, `admin_view_role`) |
| Ob’ekt | `Problem.can_view / can_view_hidden / can_edit / can_publish`, `Contest.can_view / can_manage / can_see_problems`, `Submission.can_view_code`, `ProjectSubmission.can_view` |
| Middleware | `ForcePasswordChangeMiddleware`, `SuperadminOTPMiddleware` |

Har bir qator uchun testlar: `panel/tests.py` (`PanelAccessMatrixTests`), `core/tests.py`, `problems/tests.py`,
`contests/tests.py`, `accounts/test_security.py`.
