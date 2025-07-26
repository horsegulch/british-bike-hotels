# UI Style Guide: BritishBikeHotels.com

This guide provides the core visual components and utility classes for building the frontend. We are using **Tailwind CSS**.

---

## 1. Color Palette

- **Primary (Slate Blue / Charcoal):** `#2c3e50`
  - Usage: Main text, footers, dark UI elements.
  - Tailwind: `text-slate-800`, `bg-slate-800` (approximate)
- **Accent (Amber / Gold):** `#ffc107`
  - Usage: Call-to-action buttons, highlights, featured markers.
  - Tailwind: `text-amber-400`, `bg-amber-400`
- **Background (Light Off-White):** `#f8f9fa`
  - Usage: Main page backgrounds.
  - Tailwind: `bg-gray-50`
- **Secondary/Muted Text:** `#6c757d`
  - Usage: Subheadings, meta information.
  - Tailwind: `text-gray-500`

---

## 2. Typography

- **Headings & UI (Poppins):** Use for all titles, buttons, and navigation items.
- **Body (Lora):** Use for descriptions and blog post content.

```html
<!-- You would import these from Google Fonts in your base.html -->
<h1 class="font-poppins text-4xl font-bold text-slate-800">Main Heading</h1>
<p class="font-lora text-base text-gray-700 leading-relaxed">This is a paragraph of body text...</p>
```

---

## 3. UI Components (HTML & Tailwind CSS)

### Primary Button

```html
<button class="bg-amber-400 text-slate-800 font-poppins font-bold py-3 px-6 rounded-lg shadow-md hover:bg-amber-500 transform hover:-translate-y-0.5 transition-all duration-200 ease-in-out">
  View Routes
</button>
```

### Secondary Button

```html
<button class="bg-gray-200 text-slate-800 font-poppins font-semibold py-2 px-5 rounded-lg hover:bg-gray-300 transition-colors duration-150">
  Add to Trip
</button>
```

### Hotel Summary Card (for map sidebar)

```html
<div class="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-200">
  <!-- Optional Image -->
  <img src="https://placehold.co/400x200/2c3e50/f8f9fa?text=Hotel+Image" alt="Hotel View" class="w-full h-40 object-cover">
  <div class="p-5">
    <h3 class="font-poppins text-xl font-bold text-slate-800">The Grand Brighton</h3>
    <div class="flex items-center mt-2">
      <!-- Star for featured hotels -->
      <svg class="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20"><path d="M10 15l-5.878 3.09 1.123-6.545L.489 7.91l6.572-.955L10 1l2.939 5.955 6.572.955-4.756 3.635 1.123 6.545z"></path></svg>
      <span class="font-poppins text-sm font-semibold text-amber-500 ml-1">Featured Partner</span>
    </div>
    <p class="font-lora text-gray-600 mt-3 text-sm">
      Iconic Victorian hotel on the Brighton seafront, offering luxurious accommodation...
    </p>
    <button class="w-full mt-4 bg-slate-800 text-white font-poppins font-bold py-3 px-6 rounded-lg hover:bg-slate-700 transition-colors">
      View Profile
    </button>
  </div>
</div>
```
