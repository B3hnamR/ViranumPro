User
در این بخش، پروفایل کاربر، تاریخچه سفارش‌ها و تاریخچه پرداخت‌ها قرار دارد و همه Endpointها با هدرها و نمونه‌ها آمده‌اند.
همچنین محدودیت قیمت خرید (Prices limit) برای هر محصول در سه عملیات فهرست، ایجاد/به‌روزرسانی و حذف ارائه شده است.

Title: User - Balance (Profile)
Method: GET
Endpoint: https://5sim.net/v1/user/profile
Description: Provides profile data: email, balance and rating.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Response fields:
- id: number — User ID
- email: string — User email
- balance: number — Balance
- rating: number — Rating
- default_country: object — Default country
- default_country.name: string — Country name
- default_country.iso: string — ISO country code
- default_country.prefix: string — Mobile prefix
- default_operator: object — Default operator
- default_operator.name: string — Operator name
- frozen_balance: number — Frozen balance
- default_forwarding_number: string — Default forwarding number
- vendor: string — Vendor name

Request example (curl):
curl "https://5sim.net/v1/user/profile" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "id": 1,
  "email": "[email protected]",
  "vendor": "demo",
  "default_forwarding_number": "78009005040",
  "balance": 100,
  "rating": 96,
  "default_country": { "name": "russia", "iso": "ru", "prefix": "+7" },
  "default_operator": { "name": "" },
  "frozen_balance": 0
}

Title: User - Order history
Method: GET
Endpoint: https://5sim.net/v1/user/orders?category=$category
Description: Provides orders history by chosen category.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Query parameters:
- category: string (required) — 'hosting' | 'activation'
- limit: string (optional) — Pagination limit
- offset: string (optional) — Pagination offset
- order: string (optional) — Field to order by
- reverse: string (optional) — true/false for reverse order

Response fields:
- Data: array — Orders list
- ProductNames: array — Products list
- Statuses: array — Statuses list
- Total: number — Orders count

Request example (curl):
curl "https://5sim.net/v1/user/orders?category=hosting&limit=15&offset=0&order=id&reverse=true" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "Data": [
    {
      "id": 53533933,
      "phone": "+79085895281",
      "operator": "tele2",
      "product": "aliexpress",
      "price": 2,
      "status": "BANNED",
      "expires": "2020-06-28T16:32:43.307041Z",
      "sms": [],
      "created_at": "2020-06-28T16:17:43.307041Z",
      "country": "russia"
    }
  ],
  "ProductNames": [],
  "Statuses": [],
  "Total": 3
}


Title: User - Payments history
Method: GET
Endpoint: https://5sim.net/v1/user/payments
Description: Provides payments history.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Query parameters:
- limit: string (optional) — Pagination limit
- offset: string (optional) — Pagination offset
- order: string (optional) — Field to order by
- reverse: string (optional) — true/false for reverse order

Response fields:
- Data: array — Payments list
- PaymentProviders: array — Names of payment systems
- PaymentTypes: array — Payments types
- Total: number — Payments count

Request example (curl):
curl "https://5sim.net/v1/user/payments?limit=15&offset=0&order=id&reverse=true" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "Data": [
    {
      "ID": 30011934,
      "TypeName": "charge",
      "ProviderName": "admin",
      "Amount": 100,
      "Balance": 100,
      "CreatedAt": "2020-06-24T15:37:08.149895Z"
    }
  ],
  "PaymentTypes": [{ "Name": "charge" }],
  "PaymentProviders": [{ "Name": "admin" }],
  "Total": 1
}


Prices limit
اینجا عملیات مربوط به محدودیت قیمت برای خرید هر محصول قرار دارد: دریافت فهرست، ایجاد/به‌روزرسانی و حذف محدودیت قیمت هر محصول.
نمونه‌های کامل درخواست و پاسخ و فیلدها مطابق مستندات رسمی آمده است.


Title: Prices limit - Get a list
Method: GET
Endpoint: https://5sim.net/v1/user/max-prices
Description: Get a list of established price limits.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Response fields:
- id: number — ID
- product: string — Product name
- price: number — Price
- created_at: date string — Object creation datetime

Request example (curl):
curl "https://5sim.net/v1/user/max-prices" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "id": 14,
  "product": "telegram",
  "price": 11,
  "CreatedAt": "2020-06-24T15:37:08.149895Z"
}



Title: Prices limit - Create or update
Method: POST
Endpoint: https://5sim.net/v1/user/max-prices

Headers:
- Authorization: Bearer $token
- Accept: application/json

Body parameters:
- product_name: string (required) — Product name
- price: number (required) — Price

Request example (curl):
curl -X POST "https://5sim.net/v1/user/max-prices" \
  -d '{"product_name": "telegram", "price": 30}' \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"



Title: Prices limit - Delete
Method: DELETE
Endpoint: https://5sim.net/v1/user/max-prices

Headers:
- Authorization: Bearer $token
- Accept: application/json

Body parameters:
- product_name: string (required) — Product name

Request example (curl):
curl -X DELETE "https://5sim.net/v1/user/max-prices" \
  -d '{"product_name": "telegram"}' \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"


Products and prices
این بخش شامل دریافت فهرست محصولات با قیمت و موجودی، و چهار حالت استعلام قیمت‌ها: کلی، بر اساس کشور، بر اساس محصول، و ترکیبی کشور+محصول می‌باشد.
تمام پاسخ‌ها شامل قیمت، تعداد موجود، و نرخ تحویل است و هدر پذیرش JSON نیاز است.



Title: Products - List by country/operator
Method: GET
Endpoint: https://5sim.net/v1/guest/products/$country/$operator
Description: Name, price, quantity of all products available to buy.

Headers:
- Accept: application/json

URL parameters:
- country: string (required) — "any" for any country
- operator: string (required) — "any" for any operator

Response fields:
- Category: string — activation/hosting
- Qty: number — Available quantity
- Price: number — Price

Request example (curl):
curl "https://5sim.net/v1/guest/products/$country/$operator" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "1day": { "Category": "hosting", "Qty": 14, "Price": 80 },
  "vkontakte": { "Category": "activation", "Qty": 133, "Price": 21 }
}



Title: Prices - All
Method: GET
Endpoint: https://5sim.net/v1/guest/prices
Description: Returns product prices (nested by country → product → operator).

Headers:
- Accept: application/json

Response fields:
- cost: float — Virtual number price (2 decimals)
- count: number — Available quantity
- rate: float — Delivery percentage (2 decimals), omitted < 20% or few orders

Request example (curl):
curl "https://5sim.net/v1/guest/prices" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "russia": {
    "1688": {
      "beeline": { "cost": 4, "count": 1260, "rate": 99.99 },
      "lycamobile": { "cost": 4, "count": 935, "rate": 99.99 },
      "matrix": { "cost": 4, "count": 0, "rate": 99.99 }
    }
  }
}



Title: Prices - By country
Method: GET
Endpoint: https://5sim.net/v1/guest/prices?country=$country
Description: Returns product prices by country.

Headers:
- Accept: application/json

Query parameters:
- country: string (required) — Country name

Response fields:
- cost: float — Price
- count: number — Available quantity
- rate: float — Delivery percentage

Request example (curl):
curl "https://5sim.net/v1/guest/prices?country=$country" \
  -H "Accept: application/json"



Title: Prices - By product
Method: GET
Endpoint: https://5sim.net/v1/guest/prices?product=$product
Description: Returns prices for a specific product.

Headers:
- Accept: application/json

Query parameters:
- product: string (required) — Product name

Response fields:
- cost: float — Price
- count: number — Available quantity
- rate: float — Delivery percentage

Request example (curl):
curl "https://5sim.net/v1/guest/prices?product=$product" \
  -H "Accept: application/json"



Title: Prices - By country and product
Method: GET
Endpoint: https://5sim.net/v1/guest/prices?country=$country&product=$product
Description: Returns prices by country and specific product.

Headers:
- Accept: application/json

Query parameters:
- country: string (required) — Country name
- product: string (required) — Product name

Response fields:
- cost: float — Price
- count: number — Available quantity
- rate: float — Delivery percentage

Request example (curl):
curl "https://5sim.net/v1/guest/prices?country=$country&product=$product" \
  -H "Accept: application/json"



Purchase
این بخش خرید شماره برای Activation، خرید شماره Hosting، و خرید مجدد شماره قبلی (Reuse) را شامل می‌شود.
در خرید Activation می‌توان پارامترهای اختیاری مانند forwarding، voice، reuse و maxPrice را نیز اعمال کرد.


Title: Purchase - Buy activation number
Method: GET
Endpoint: 
- https://5sim.net/v1/user/buy/activation/$country/$operator/$product
- https://5sim.net/v1/user/buy/activation/$country/$operator/$product?forwarding=$forwarding&number=$number&reuse=$reuse&voice=$voice&ref=$ref&maxPrice=$maxPrice
Description: Order a phone number for a specific product (activation).

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- country: string (required) — "any" allowed
- operator: string (required) — "any" allowed
- product: string (required) — Product name

Query parameters (optional):
- forwarding: string — Enable call forwarding (0/1)
- number: string — Forward-to number (RU only, 11 digits, no '+')
- reuse: string — "1" to buy with reuse ability if available
- voice: string — "1" to allow robot call if available
- ref: string — Referral key
- maxPrice: string — Per-request max price (overrides "Max purchase price" setting; works only if operator="any")

Response fields:
- id: number — Order ID
- phone: string — Phone number
- operator: string — Operator
- product: string — Product
- price: number — Price
- status: string — Order status
- expires: date string — Expiration time
- sms: array — SMS list
- created_at: date string — Creation time
- forwarding: boolean — Forwarding enabled
- forwarding_number: string — Call forwarding number
- country: string — Country name

Possible errors:
- not enough user balance
- not enough rating
- select country
- select operator
- bad country
- bad operator
- no product
- server offline

Request example (curl):
curl "https://5sim.net/v1/user/buy/activation/$country/$operator/$product" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "id": 11631253,
  "phone": "+79000381454",
  "operator": "beeline",
  "product": "vkontakte",
  "price": 21,
  "status": "PENDING",
  "expires": "2018-10-13T08:28:38.809469028Z",
  "sms": null,
  "created_at": "2018-10-13T08:13:38.809469028Z",
  "forwarding": false,
  "forwarding_number": "",
  "country": "russia"
}



Title: Purchase - Buy hosting number
Method: GET
Endpoint: https://5sim.net/v1/user/buy/hosting/$country/$operator/$product
Description: Buy a hosting number (products: 3hours, 1day, etc.).

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- country: string (required) — "any" allowed
- operator: string (required) — "any" allowed
- product: string (required) — Hosting product name (e.g., 3hours, 1day)

Response fields:
- id, phone, product, price, status, expires, sms[], created_at

Possible errors:
- no free phones
- not enough user balance
- not enough rating
- select country
- select operator
- bad country
- bad operator
- no product
- server offline

Request example (curl):
curl "https://5sim.net/v1/user/buy/hosting/$country/$operator/$product" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "id": 1,
  "phone": "+79008001122",
  "product": "1day",
  "price": 1,
  "status": "PENDING",
  "expires": "1970-12-01T03:00:00.000000Z",
  "sms": [
    {
      "id": 3027531,
      "created_at": "1970-12-01T17:23:25.106597Z",
      "date": "1970-12-01T17:23:15Z",
      "sender": "Facebook",
      "text": "Use 415127 as your login code",
      "code": "415127"
    }
  ],
  "created_at": "1970-12-01T00:00:00.000000Z"
}



Title: Purchase - Re-buy number (Reuse)
Method: GET
Endpoint: https://5sim.net/v1/user/reuse/$product/$number

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- product: string (required) — Product name
- number: string (required) — Phone number (4–15 digits, without '+')

Possible responses (errors/info):
- no free phones
- select operator
- not enough user balance
- bad country
- bad operator
- server offline
- not enough rating
- no product
- reuse not possible
- reuse false
- reuse expired

Request example (curl):
curl "https://5sim.net/v1/user/reuse/$product/$number" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"



Order management
این بخش شامل بررسی وضعیت سفارش و دریافت SMS، اتمام، لغو، بن‌کردن سفارش و مشاهده صندوق ورودی SMS است.
هر Endpoint با فیلدهای پاسخ استاندارد سفارش (id, phone, product, price, status, expires, sms, ...) مستند شده است.




Title: Order - Check (Get SMS)
Method: GET
Endpoint: https://5sim.net/v1/user/check/$id

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- id: string (required) — Order ID

Response fields (order object):
- id, created_at, phone, product, price, status, expires, sms[], forwarding, forwarding_number, country

Request example (curl):
curl "https://5sim.net/v1/user/check/$id" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"


Title: Order - Finish
Method: GET
Endpoint: https://5sim.net/v1/user/finish/$id

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- id: string (required) — Order ID

Response fields:
- id, created_at, phone, product, price, status, expires, sms[], forwarding, forwarding_number, country

Request example (curl):
curl "https://5sim.net/v1/user/finish/$id" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"



Title: Order - Cancel
Method: GET
Endpoint: https://5sim.net/v1/user/cancel/$id

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- id: string (required) — Order ID

Response fields:
- id, created_at, phone, product, price, status, expires, sms[], forwarding, forwarding_number, country

Request example (curl):
curl "https://5sim.net/v1/user/cancel/$id" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"



Title: Order - Ban
Method: GET
Endpoint: https://5sim.net/v1/user/ban/$id

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- id: string (required) — Order ID

Response fields:
- id, created_at, phone, product, price, status, expires, sms[], forwarding, forwarding_number, country

Request example (curl):
curl "https://5sim.net/v1/user/ban/$id" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"



Title: Order - SMS inbox list
Method: GET
Endpoint: https://5sim.net/v1/user/sms/inbox/$id
Description: Get SMS inbox list by order's id.

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- id: string (required) — Order ID

Response fields:
- Data: array — SMS list
- Total: number — SMS count

Request example (curl):
curl "https://5sim.net/v1/user/sms/inbox/$id" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{
  "Data": [
    {
      "ID": 844928,
      "created_at": "2017-09-05T15:48:33.763297Z",
      "date": "2017-09-05T15:48:27Z",
      "sender": "+79998887060",
      "text": "12345",
      "code": "",
      "is_wave": false,
      "wave_uuid": ""
    }
  ],
  "Total": 1
}


Notifications
این بخش دریافت اعلان‌های متنی عمومی را بر اساس زبان در اختیار می‌گذارد و نیازمند تعیین زبان است.
هدر پذیرش JSON الزامی است و پاسخ شامل فیلد text می‌باشد.



Title: Notifications - Get
Method: GET
Endpoint: https://5sim.net/v1/guest/flash/$lang

Headers:
- Authorization: Bearer $token
- Accept: application/json

URL parameters:
- lang: string (required) — ru/en

Response fields:
- text: string — Notification text

Request example (curl):
curl "https://5sim.net/v1/guest/flash/$lang" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example:
{ "text": "...notification text..." }


Vendor
این بخش اطلاعات فروشنده، موجودی کیف‌پول‌ها، تاریخچه سفارش‌ها و پرداخت‌ها و همچنین ایجاد برداشت وجه برای شریک را پوشش می‌دهد.
تمام Endpointها Bearer token می‌خواهند و نمونه‌های درخواست/پاسخ درج شده‌اند.

Title: Vendor - Statistic (Profile)
Method: GET
Endpoint: https://5sim.net/v1/user/vendor

Headers:
- Authorization: Bearer $token
- Accept: application/json

Response fields:
- id, email, vendor, default_forwarding_number, balance, rating,
  default_country { name, iso, prefix }, default_operator { name }, frozen_balance


Title: Vendor - Wallets reserve
Method: GET
Endpoint: https://5sim.net/v1/vendor/wallets
Description: Available reserves currency for partner.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Response fields:
- fkwallet: number
- payeer: number
- unitpay: number

Request example (curl):
curl "https://5sim.net/v1/vendor/wallets" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"

Response example (truncated JSON):
{ "fkwallet": 43339.55, "payeer": 2117.32, "unitpay": 97.6 }



Title: Vendor - Orders history
Method: GET
Endpoint: https://5sim.net/v1/vendor/orders?category=$category
Description: Provides vendor's orders history by chosen category.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Query parameters:
- category: string (required) — 'hosting' | 'activation'
- limit, offset, order, reverse: string (optional) — Pagination options

Response fields:
- Data: array — Orders
- ProductNames: array — Products
- Statuses: array — Statuses
- Total: number — Count



Title: Vendor - Payments history
Method: GET
Endpoint: https://5sim.net/v1/vendor/payments
Description: Provides vendor's payments history.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Query parameters:
- limit, offset, order, reverse: string (optional) — Pagination options

Response fields:
- Data: array — Payments
- PaymentProviders: array — Payment systems
- PaymentStatuses: array — Statuses
- PaymentTypes: array — Types
- Total: number — Count

Request example (curl):
curl "https://5sim.net/v1/vendor/payments?limit=15&offset=0&order=id&reverse=true" \
  -H "Authorization: Bearer $token" \
  -H "Accept: application/json"


Title: Vendor - Create payouts (Withdraw)
Method: POST
Endpoint: https://5sim.net/v1/vendor/withdraw
Description: Create payouts for a partner.

Headers:
- Authorization: Bearer $token
- Content-Type: application/json

Body parameters:
- receiver: string (required) — Receiver
- method: string (required) — Output method (visa / qiwi / yandex)
- amount: string (required) — Amount
- fee: string (required) — Payment system (fkwallet / payeer / unitpay)

Request example (curl):
curl -X POST "https://5sim.net/v1/vendor/withdraw" \
  -d '{"receiver":"1","method":"qiwi","amount":"1","fee":"unitpay"}' \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json"



Countries list
این بخش فهرست کشورها را با ISO و نام به دو زبان و اپراتورهای موجود برمی‌گرداند و نیازمند هدر پذیرش JSON است.
Endpoint مهم برای دریافت پوشش سرویس در کشورهای مختلف همین آدرس است.


Title: Countries - List
Method: GET
Endpoint: https://5sim.net/v1/guest/countries
Description: Returns a list of countries with available operators for purchase.

Headers:
- Authorization: Bearer $token
- Accept: application/json

Response fields:
- iso: object — ISO country code
- text_en: string — Country name in English
- text_ru: string — Country name in Russian
- prefix: object — Dial prefixes
- available operators per country (nested keys)

Response example (truncated JSON):
{
  "afghanistan": {
    "iso": { "af": 1 },
    "prefix": { "+93": 1 },
    "text_en": "Afghanistan",
    "text_ru": "Афганистан",
    "virtual18": { "activation": 1 },
    "virtual21": { "activation": 1 },
    "virtual23": { "activation": 1 },
    "virtual4":  { "activation": 1 }
  }
}



Order statuses
در این بخش وضعیت‌های ممکن سفارش‌ها تعریف شده‌اند که در پاسخ‌های سفارش استفاده می‌شوند.
این وضعیت‌ها شامل حالت‌های آماده‌سازی، انتظار پیامک، لغو، تایم‌اوت، اتمام و بن شدن شماره هستند.



Order statuses:
- PENDING   — Preparation
- RECEIVED  — Waiting of receipt of SMS
- CANCELED  — Is cancelled
- TIMEOUT   — A timeout
- FINISHED  — Is complete
- BANNED    — Number banned, when number already used


Products list
این بخش لیست محصولات Activation و Hosting را نشان می‌دهد؛ در Hosting نمونه‌هایی مثل 3hours، 1day، 10days، 1month آمده است.
در Activation، جدول سرویس‌ها به همراه نام API 5SIM در مستندات ارائه شده است.



Products:
- Activation: See table of "Service | API 5SIM"
- Hosting:
  - 3hours
  - 1day
  - 10days
  - 1month


Operators list
برای دریافت فهرست اپراتورها نیاز به احراز هویت است و جزئیات از همین صفحه مستندات قابل مشاهده است.
Endpoint‌های مرتبط با اپراتورها بسته به کشور و دسترسی پس از احراز هویت در پاسخ‌ها بازگردانده می‌شوند.


Operators:
- Note: Authorization required to get operators list.



Structure of SMS
ساختار شیء SMS در پاسخ سفارش‌ها مستند شده و شامل زمان ایجاد، زمان دریافت، فرستنده، متن و کد استخراج‌شده است.
نمونه پاسخ در بخش‌های خرید و میزبانی هم تکرار شده که الگوی یکسانی دارد.



SMS object fields:
- created_at: date string — When SMS was created
- date: date string — When SMS received
- sender: string — Sender name
- text: string — Text of SMS
- code: string — Received activation code

Example (truncated):
{
  "sms": [
    {
      "created_at": "1970-12-01T17:23:25.106597Z",
      "date": "1970-12-01T17:23:15Z",
      "sender": "Facebook",
      "text": "Use 415127 as your login code",
      "code": "415127"
    }
  ]
}


Limits
تیتر Limits در انتهای صفحه آمده است و به محدودیت‌های استفاده اشاره دارد، اما جزئیات عملیاتی مستقلی در همین بخش نمایش داده نشده است.
برای محدودیت‌های خرید در سطح قیمت، از بخش Prices limit استفاده می‌شود که در بالا پوشش داده شد.

Limits:
- Refer to "Prices limit" for per-product max purchase price controls.
- Other usage constraints are implied by errors/statuses in endpoints.


Rating
سیستم امتیازدهی (Rating) در مستندات توضیح داده شده و سقف امتیاز 96 است؛ امتیاز اولیه کاربران جدید نیز 96 می‌باشد.
کاهش امتیاز می‌تواند باعث محدودیت سفارش برای 24 ساعت شود و پس از آن به مقدار اولیه بازمی‌گردد.



Rating system:
- Current rating is shown in account settings (General tab).
- Initial rating: 96; Maximum rating: 96.
- Actions → Rating impact:
  - Account replenishment: +8
  - Completed before code elapsed time: +0.5
  - Automatically completed after allowed time: +0.4
  - Timeout: -0.15
  - Canceled purchase: -0.1
  - Number sent to ban: -0.1
- If rating drops to 0: ordering is blocked for 24 hours, then returns to 96.






