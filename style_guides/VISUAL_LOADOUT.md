# 🎨 VISUAL LOADOUT — UI/UX & Design Guide

This is a workshop, not a showroom. The way this place looks should feel like it was built for work. Every button, every color, every font has a job to do. If it ain’t useful, it gets tossed in the scrap heap.

This guide is our blueprint. It keeps the place lookin’ sharp, consistent, and ready for action.

---

## 1. Color Palette & Mood

Our colors are pulled from a greasy engine bay, a rusty chassis, and a midnight highway. The mood is dark, focused, and utilitarian.

- **Primary Background:** `#121417` (Almost Black) - The foundation. Like the frame of a truck.
- **Secondary Background:** `#1E2226` (Dark Gray) - For cards and panels. Gives a little depth.
- **Primary Text:** `#F8F9FA` (Off-White) - Easy on the eyes for long nights.
- **Accent / Primary Action:** `#0D6EFD` (Bootstrap Blue) - For buttons that do stuff. A splash of color in the dark.
- **Success:** `#198754` (Green) - For when things go right.
- **Warning:** `#FFC107` (Yellow) - For when you need to pay attention.
- **Danger / Error:** `#DC3545` (Red) - For when things are busted.
- **Muted Text / Borders:** `#495057` (Gray) - For stuff that ain’t the main event.

## 2. Typography

We use fonts that are clean, readable, and don’t mess around.

- **Primary Font:** `Inter` (or a system sans-serif like Helvetica/Arial as a fallback). It’s a workhorse font — strong and easy to read.
- **Monospace Font:** `Courier New` or `monospace`. For code, data, or anything that needs to look like a system readout.

### Hierarchy
- **`<h1>`:** Main page titles. Big, bold, and in charge.
- **`<h2>`, `<h3>`:** Section headers. Break up the page.
- **`<p>`:** Body text. The meat and potatoes.
- **`<small>` or `.text-muted`:** For footnotes, captions, or asides.

## 3. Layout & Spacing

Give things room to breathe, but don’t waste space. A clean workspace is a productive workspace.

- **Grid:** We use Bootstrap’s 12-column grid. Learn it, use it.
- **Padding:** Use consistent padding around elements. `1rem` or `1.5rem` is a good starting point.
- **Whitespace:** Don’t be afraid of it. It’s not empty space; it’s a tool for focus.

## 4. Buttons, Icons, and Components

Every part has a purpose.

- **Buttons:** Should look like buttons. Solid, clear, and with a strong call to action. Use Bootstrap’s default styles (`.btn-primary`, `.btn-secondary`).
- **Icons:** We use Bootstrap Icons. They’re simple, clean, and look like they belong on a dashboard. Use them to clarify actions, not just for decoration.
- **Cards:** Our main component for organizing information. They should be clean, with clear headers and minimal fluff. The `swtoEagleWhite.png` can be used as a subtle watermark on cards for branding.

## 5. Accessibility Standards

Just ‘cause it’s gritty doesn’t mean it’s gotta be hard to use. Everyone’s welcome in this workshop.

- **Contrast:** Ensure text has enough contrast against its background. Use a tool to check it.
- **Alt Text:** All images that convey information need descriptive `alt` text.
- **Labels:** All form inputs need clear, associated `<label>`s.
- **Keyboard Navigation:** Make sure you can get around the site with just a keyboard.

## 6. Example Layout Guidance

- **Guest Homepage:** Big, bold headline. A short, punchy intro. Prominent login/register buttons. The SWTO Eagle logo should be featured prominently but tastefully.
- **Dashboard:** A grid of cards. Each card is a self-contained tool or link. Important info should be at the top.
- **Forms:** Clean and simple. Labels on top of inputs. Clear instructions. Validation feedback should be immediate and helpful.

## 7. Design Notes

- **Functional Over Flashy:** If an animation or effect doesn’t help the user, get rid of it.
- **Gritty, Not Dirty:** The design should feel like a well-used but well-maintained tool, not a piece of junk.
- **Data-First:** For dashboards, the data is the star of the show. Design everything to make the numbers easy to read and understand.

---
*This is our visual loadout. Stick to it, and you’ll build something that looks as good as it runs.*
