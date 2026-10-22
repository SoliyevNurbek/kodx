# kodx.uz

«Dasturlash va sun’iy intellekt asoslari» kursi o‘quvchilari uchun masalalar,
misollar va uyga vazifalarni yechish platformasi (Codeforces, Kep.uz, Robocontest
uslubida). Muallif: Nurbek Soliyev.

> Holat: **1-bosqich — poydevor** (Django, MySQL, rollar, audit, admin).

## Texnologiyalar

- Python 3.12, Django 5.2
- MySQL 8 (utf8mb4, `STRICT_TRANS_TABLES`)
- Argon2 parol xeshlash
- Sozlamalar `.env` orqali (python-dotenv)
- Keyingi bosqichda: Judge0 — kodni izolyatsiyalangan tekshirish

## O‘rnatish (lokal)

1. Repozitoriyni klonlash va virtual muhit:

   ```bash
   git clone https://github.com/SoliyevNurbek/kodx.git
   cd kodx
   python -m venv venv
   venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: venv/bin/python
   ```

2. MySQL’da baza va alohida foydalanuvchi (root bilan ishlamang):

   ```sql
   CREATE DATABASE kodx CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'kodx_user'@'localhost' IDENTIFIED BY '<kuchli-parol>';
   GRANT ALL PRIVILEGES ON kodx.* TO 'kodx_user'@'localhost';
   GRANT ALL PRIVILEGES ON test_kodx.* TO 'kodx_user'@'localhost';  -- testlar uchun
   ```

3. Sozlamalar: `.env.example` dan `.env` nusxasini oling va to‘ldiring.

4. Migratsiya, administrator va ishga tushirish:

   ```bash
   venv/Scripts/python manage.py migrate
   venv/Scripts/python manage.py createsuperuser
   venv/Scripts/python manage.py runserver
   ```

   Admin panel: <http://127.0.0.1:8000/admin/>

5. Testlar:

   ```bash
   venv/Scripts/python manage.py test
   ```

## Rollar

Har yuqori rol pastdagilarning barcha huquqlarini o‘z ichiga oladi
(`user.has_role_at_least(Role.JURY)` va h.k.).

| Daraja | Rol | Huquqlar |
|---|---|---|
| 1 | user | profil, masalalar, yechim yuborish, o‘z urinishlari, reyting |
| 2 | jury | + kontest yaratish va o‘z kontestlarini boshqarish |
| 3 | jury_pro | + masala va test qo‘shish; faqat o‘z masalalarini tahrirlash |
| 4 | moderator | + barcha urinishlar va testlarni ko‘rish; jury/jury_pro rolini berish; rol so‘rovlarini tasdiqlash |
| 5 | superadmin | + tizim sozlamalari, barcha rollar |

Hech kim (superadmin ham) foydalanuvchi parolini ko‘ra olmaydi — faqat
qayta tiklashga majburlash mumkin. Muhim admin harakatlari `audit.AuditLog`
jurnaliga yoziladi.

## Tuzilma

```
config/        Django sozlamalari va URL’lar
accounts/      User (rollar), RoleRequest
audit/         AuditLog va log_action()
courses/       kurs, modul, dars (2-bosqich)
problems/      masalalar va testlar (3-bosqich)
submissions/   yechimlar va Judge0 (4-bosqich)
contests/      kontestlar (6-bosqich)
```
