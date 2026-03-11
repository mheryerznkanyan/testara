# Landing Page Implementation Plan

**Apple-style with heavy animations** 🎬

---

## 🎬 **All Animations (Detailed)**

### **1. Hero Section**

**Ambient Gradient Background:**
```jsx
// Slowly pulsing gradient orbs
<div className="absolute inset-0">
  <motion.div
    className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 blur-3xl"
    animate={{
      scale: [1, 1.2, 1],
      opacity: [0.3, 0.5, 0.3],
    }}
    transition={{
      duration: 8,
      repeat: Infinity,
      ease: "easeInOut"
    }}
  />
</div>
```

**Headline Fade-in:**
```jsx
<motion.h1
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
>
  Stop Writing XCUITests
</motion.h1>
```

**Code Preview Float:**
```jsx
<motion.div
  initial={{ opacity: 0, y: 40 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: 1, duration: 1 }}
  whileHover={{ y: -5, scale: 1.02 }}
>
  <CodePreview />
</motion.div>
```

---

### **2. Interactive Code Demo**

**Typing Animation:**
```tsx
const [text, setText] = useState("")
const fullText = "test login with invalid password"

useEffect(() => {
  let i = 0
  const timer = setInterval(() => {
    if (i <= fullText.length) {
      setText(fullText.slice(0, i))
      i++
    } else {
      clearInterval(timer)
    }
  }, 80) // Realistic typing speed
  return () => clearInterval(timer)
}, [])
```

**Generated Code Reveal:**
```jsx
<motion.div
  initial={{ opacity: 0, height: 0 }}
  animate={{ opacity: 1, height: "auto" }}
  transition={{ delay: 3, duration: 0.6 }}
>
  <SyntaxHighlighter language="swift">
    {generatedCode}
  </SyntaxHighlighter>
</motion.div>
```

**Quality Score Pop-in:**
```jsx
<motion.div
  initial={{ scale: 0, rotate: -180 }}
  animate={{ scale: 1, rotate: 0 }}
  transition={{ 
    delay: 4,
    type: "spring",
    stiffness: 260,
    damping: 20
  }}
>
  <QualityBadge score={92} grade="A" />
</motion.div>
```

---

### **3. Features Bento Grid**

**Staggered Entrance:**
```jsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const item = {
  hidden: { y: 20, opacity: 0 },
  show: { y: 0, opacity: 1 }
}

<motion.div
  variants={container}
  initial="hidden"
  whileInView="show"
  viewport={{ once: true, margin: "-100px" }}
>
  {features.map(feature => (
    <motion.div key={feature.id} variants={item}>
      <FeatureCard {...feature} />
    </motion.div>
  ))}
</motion.div>
```

**Card Hover Effect:**
```jsx
<motion.div
  className="feature-card"
  whileHover={{
    y: -8,
    scale: 1.02,
    boxShadow: "0 20px 40px rgba(0, 112, 227, 0.2)"
  }}
  transition={{ duration: 0.3 }}
>
  {/* Card content */}
</motion.div>
```

**Icon Animation:**
```jsx
<motion.div
  animate={{
    rotate: [0, 10, -10, 0],
  }}
  transition={{
    duration: 2,
    repeat: Infinity,
    ease: "easeInOut"
  }}
>
  <Icon />
</motion.div>
```

---

### **4. How It Works (Scroll-Triggered)**

**Sticky Scroll Animation:**
```jsx
const { scrollYProgress } = useScroll({
  target: ref,
  offset: ["start end", "end start"]
})

const y = useTransform(scrollYProgress, [0, 1], [100, -100])

<motion.div style={{ y }}>
  <StepContent />
</motion.div>
```

**Step Reveal:**
```jsx
const steps = [
  { title: "Describe", delay: 0 },
  { title: "We Read", delay: 0.2 },
  { title: "Get Code", delay: 0.4 }
]

{steps.map(step => (
  <motion.div
    key={step.title}
    initial={{ opacity: 0, x: -50 }}
    whileInView={{ opacity: 1, x: 0 }}
    viewport={{ once: true }}
    transition={{ delay: step.delay, duration: 0.6 }}
  >
    <Step {...step} />
  </motion.div>
))}
```

**Number Count-up:**
```jsx
<motion.span
  initial={{ opacity: 0 }}
  whileInView={{ opacity: 1 }}
  viewport={{ once: true }}
>
  <CountUp end={30} duration={2} suffix="s" />
</motion.span>
```

---

### **5. Pricing Card**

**Glass Morphism with Blur:**
```jsx
<motion.div
  className="backdrop-blur-xl bg-white/5 border border-white/10"
  initial={{ opacity: 0, scale: 0.9 }}
  whileInView={{ opacity: 1, scale: 1 }}
  viewport={{ once: true }}
  transition={{ duration: 0.6 }}
>
  <PricingContent />
</motion.div>
```

**Gradient Border Animation:**
```jsx
<motion.div
  className="relative"
  animate={{
    background: [
      "linear-gradient(0deg, rgba(0,112,227,0.5), rgba(124,58,237,0.5))",
      "linear-gradient(360deg, rgba(124,58,237,0.5), rgba(0,112,227,0.5))"
    ]
  }}
  transition={{ duration: 3, repeat: Infinity }}
>
  {/* Card */}
</motion.div>
```

---

### **6. CTA Button**

**Shimmer Effect:**
```jsx
<motion.button
  className="relative overflow-hidden"
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  <motion.div
    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
    animate={{
      x: ["-100%", "200%"]
    }}
    transition={{
      duration: 1.5,
      repeat: Infinity,
      repeatDelay: 1
    }}
  />
  Join Free Pilot →
</motion.button>
```

---

### **7. Scroll-Based Parallax**

**Background Moves Slower:**
```jsx
const { scrollY } = useScroll()
const y = useTransform(scrollY, [0, 1000], [0, -200])

<motion.div style={{ y }} className="absolute inset-0">
  <GradientBackground />
</motion.div>
```

---

### **8. Page Transitions**

**Smooth Page Load:**
```jsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  transition={{ duration: 0.5 }}
>
  <LandingPage />
</motion.div>
```

---

## 🎨 **Easing Functions (Apple-style)**

```js
// Custom easing for Apple feel
const easeInOutQuart = [0.25, 0.1, 0.25, 1]
const easeOutExpo = [0.16, 1, 0.3, 1]
const spring = { type: "spring", stiffness: 260, damping: 20 }
```

---

## 📱 **Responsive Animations**

**Reduced Motion Support:**
```jsx
const prefersReducedMotion = useReducedMotion()

<motion.div
  animate={prefersReducedMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
>
  {/* Content */}
</motion.div>
```

---

## ⚡ **Performance Optimization**

```jsx
// Will-change for smooth animations
.animated-element {
  will-change: transform, opacity;
}

// GPU acceleration
transform: translate3d(0, 0, 0);

// Lazy load heavy components
const Demo = dynamic(() => import('./Demo'), {
  ssr: false,
  loading: () => <Skeleton />
})
```

---

**Total Animations:** 15+  
**Animation Library:** Framer Motion  
**Performance:** 60 FPS on all devices

All animations follow Apple's Human Interface Guidelines for timing and easing.
