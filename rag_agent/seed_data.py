SEED_PRODUCTS = [
    {
        "name": "AirPods Pro",
        "category": "wireless earbuds",
        "price": 249.00,
        "cost": 100.00,
        "margin_floor": 30,
        "features": "Active noise cancellation, transparency mode, spatial audio, adaptive audio, personalized volume",
        "competitor": "Apple",
    },
    {
        "name": "Samsung Galaxy Buds2 Pro",
        "category": "wireless earbuds",
        "price": 229.99,
        "cost": 92.00,
        "margin_floor": 35,
        "features": "Active noise cancellation, ambient sound, IPX7 water resistance, touch controls",
        "competitor": "Samsung",
    },
    {
        "name": "Sony WF-1000XM5",
        "category": "wireless earbuds",
        "price": 299.99,
        "cost": 120.00,
        "margin_floor": 32,
        "features": "Industry-leading noise cancellation, LDAC codec, 8-hour battery, multipoint connection",
        "competitor": "Sony",
    },
    {
        "name": "Apple Watch Series 9",
        "category": "smartwatch",
        "price": 399.00,
        "cost": 160.00,
        "margin_floor": 40,
        "features": "Always-on retina display, fitness tracking, ECG, blood oxygen, emergency SOS, cellular optional",
        "competitor": "Apple",
    },
    {
        "name": "Samsung Galaxy Watch 6",
        "category": "smartwatch",
        "price": 299.99,
        "cost": 120.00,
        "margin_floor": 38,
        "features": "AMOLED display, heart rate monitor, sleep tracking, water resistant, 40+ watch faces",
        "competitor": "Samsung",
    },
    {
        "name": "Garmin Epix Gen 2",
        "category": "smartwatch",
        "price": 499.99,
        "cost": 200.00,
        "margin_floor": 35,
        "features": "AMOLED display, multi-GNSS, 11-day battery, training metrics, maps, music storage",
        "competitor": "Garmin",
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "category": "over-ear headphones",
        "price": 399.99,
        "cost": 160.00,
        "margin_floor": 33,
        "features": "Industry-leading ANC, 30-hour battery, multipoint connection, lightweight design",
        "competitor": "Sony",
    },
    {
        "name": "Bose QuietComfort 45",
        "category": "over-ear headphones",
        "price": 379.95,
        "cost": 150.00,
        "margin_floor": 32,
        "features": "Acoustic noise cancelling, comfortable design, 24-hour battery, USB-C charging",
        "competitor": "Bose",
    },
    {
        "name": "Anker Soundcore Space Q45",
        "category": "over-ear headphones",
        "price": 99.99,
        "cost": 40.00,
        "margin_floor": 45,
        "features": "Adaptive ANC, 50-hour battery, quick charge, spatial audio, lightweight",
        "competitor": "Anker",
    },
    {
        "name": "Apple AirTag",
        "category": "tracking device",
        "price": 29.00,
        "cost": 8.00,
        "margin_floor": 50,
        "features": "Find My network, precision finding, ultra wideband, replaceable battery, IP67 water resistant",
        "competitor": "Apple",
    },
]

POLICY_DOC = """
# MarginGuard Pricing and Competitive Response Policy

## Margin Floor Requirements
All products must maintain a minimum gross margin of the specified margin floor percentage.
Margin calculation: (Price - Cost) / Price * 100

## Price Matching Rules
1. We can match competitor prices if the resulting margin is >= margin floor
2. We cannot price below our cost + 5% handling buffer
3. Price changes must be approved if they reduce margin below 35%

## Feature Parity Requirements
- If competitor has feature parity within 5% of our feature set, price difference must not exceed 10%
- If competitor has 10-30% more features, we can price up to 15% higher
- If competitor has >30% more features, we must match or undercut by 5%

## Competitive Response Timeline
- Premium tier products (>$200): Response within 14 days
- Mid-tier products ($100-200): Response within 7 days
- Budget tier products (<$100): Response within 3 days

## Approval Levels
- Margin reduction 0-5%: Automatic approval if features competitive
- Margin reduction 5-10%: Product manager approval required
- Margin reduction >10%: CFO + Product manager approval required
- Below margin floor: BLOCKED - no approval possible
"""
