'use client'

import { motion } from 'framer-motion'

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      <Hero />
      <Problem />
      <Demo />
      <TechnicalMoat />
      <WorksWith />
      <Features />
      <Pricing />
      <FAQ />
      <Footer />
    </main>
  )
}

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Ambient gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        />
        <motion.div
          className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: 1
          }}
        />
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-6 py-20">
        <motion.h1
          className="text-6xl md:text-7xl font-bold text-center mb-6 tracking-tight"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          Generate Working<br />
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            XCUITests from Plain English
          </span>
        </motion.h1>

        <motion.p
          className="text-xl md:text-2xl text-gray-400 text-center mb-12 max-w-3xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
        >
          Describe a test. Testara reads your Swift code and generates<br />
          compile-ready XCUITest code in 30 seconds.
        </motion.p>

        {/* Input/Output Demo */}
        <motion.div
          className="grid md:grid-cols-2 gap-6 mb-12 max-w-4xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
        >
          <div className="glass p-6 rounded-xl">
            <div className="text-sm text-gray-400 mb-2">You type:</div>
            <div className="font-mono text-sm text-white">
              "test login with invalid password"
            </div>
          </div>
          <div className="glass p-6 rounded-xl">
            <div className="text-sm text-gray-400 mb-2">Generated:</div>
            <div className="font-mono text-sm text-green-400">
              final class LoginTests: XCTestCase {'{'}<br />
              &nbsp;&nbsp;func testLogin() {'{'} ...<br />
              {'}'}
            </div>
          </div>
        </motion.div>

        <motion.div
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9, duration: 0.8 }}
        >
          <button className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-full text-lg font-semibold transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/50">
            Request Pilot Access
          </button>
          <button className="glass hover:bg-white/10 px-8 py-4 rounded-full text-lg font-semibold transition-all duration-300">
            See Example Test →
          </button>
        </motion.div>

        <motion.p
          className="text-center text-gray-400 mt-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
        >
          🔒 Your code stays private  •  ✓ Free for 3 months  •  ✓ Setup in 5 minutes
        </motion.p>
      </div>
    </section>
  )
}

function Problem() {
  return (
    <section className="py-20 px-6 bg-gradient-to-b from-black to-gray-900">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          iOS UI tests are expensive to write,<br />brittle to maintain
        </motion.h2>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {[
            { number: '3-5×', text: 'longer to write tests than build features' },
            { number: '<20%', text: 'of UI flows get test coverage' },
            { number: 'Every sprint', text: 'tests break on refactors' }
          ].map((stat, i) => (
            <motion.div
              key={i}
              className="glass p-8 rounded-xl text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
            >
              <div className="text-4xl font-bold text-blue-400 mb-2">{stat.number}</div>
              <div className="text-gray-400">{stat.text}</div>
            </motion.div>
          ))}
        </div>

        <motion.p
          className="text-xl text-center text-gray-300 max-w-3xl mx-auto"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Most iOS teams skip UI tests entirely.<br />
          When something breaks in production, nobody saw it coming.
        </motion.p>
      </div>
    </section>
  )
}

function Demo() {
  const codeExample = `import XCTest

final class LoginTests: XCTestCase {
    func testLoginWithInvalidPassword() throws {
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(en)"]
        app.launch()
        
        // Enter invalid credentials
        let emailField = app.textFields["emailTextField"]
        XCTAssertTrue(emailField.waitForExistence(timeout: 5))
        emailField.tap()
        emailField.typeText("user@test.com")
        
        let passwordField = app.secureTextFields["passwordTextField"]
        passwordField.tap()
        passwordField.typeText("wrongpassword")
        
        // Submit
        app.buttons["loginButton"].tap()
        
        // Verify error message
        let errorLabel = app.staticTexts["errorLabel"]
        XCTAssertTrue(errorLabel.waitForExistence(timeout: 5))
        XCTAssertEqual(errorLabel.label, "Invalid password")
    }
}`

  return (
    <section className="py-20 px-6 bg-black">
      <div className="max-w-6xl mx-auto">
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Example Generated Test</h2>
          <p className="text-xl text-gray-400">From description to production-ready code in 30 seconds</p>
        </motion.div>

        <motion.div
          className="glass p-8 rounded-2xl"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <span className="text-sm text-gray-400">Input:</span>
            <code className="text-blue-400">"test login with invalid password shows error"</code>
          </div>
          
          <pre className="bg-gray-900 p-6 rounded-lg overflow-x-auto text-sm">
            <code className="text-green-400">{codeExample}</code>
          </pre>

          <div className="mt-4 flex gap-3">
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm">✓ Compiles</span>
            <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm">Quality Score: A (92/100)</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

function TechnicalMoat() {
  const features = [
    {
      icon: '🧬',
      title: 'Reads Swift Source Code',
      desc: 'Uses AST parsing to extract accessibility identifiers, view hierarchies, and navigation patterns from your actual Swift files.'
    },
    {
      icon: '🗺️',
      title: 'Maps Screen Navigation',
      desc: 'Detects NavigationLink, sheet, push patterns. Understands which screens require login and navigation prerequisites.'
    },
    {
      icon: '🔍',
      title: 'RAG-Powered Context',
      desc: 'Indexes your codebase with Chroma vector store. Finds relevant code for each test description.'
    },
    {
      icon: '✅',
      title: 'Generates Compile-Ready Tests',
      desc: 'No hallucinations. No guessed selectors. Uses only identifiers that exist in your code.'
    }
  ]

  return (
    <section className="py-20 px-6 bg-gradient-to-b from-black to-gray-900">
      <div className="max-w-6xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">How Testara Works</h2>
          <p className="text-xl text-gray-400">Unlike generic AI tools, Testara understands YOUR codebase</p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              className="glass p-8 rounded-xl hover:bg-white/10 transition-all duration-300"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -5, scale: 1.02 }}
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-400">{feature.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          className="text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <p className="text-sm text-gray-500 mb-3">Built With</p>
          <div className="flex flex-wrap justify-center gap-3">
            {['Swift AST Parsing', 'Claude Sonnet 3.5', 'LangChain', 'Chroma', 'FastAPI'].map((tech, i) => (
              <span key={i} className="px-4 py-2 bg-gray-800 rounded-full text-sm text-gray-300">
                {tech}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}

function WorksWith() {
  const compat = [
    { title: 'UI Frameworks', items: ['SwiftUI', 'UIKit'] },
    { title: 'Testing', items: ['XCTest', 'XCUITest'] },
    { title: 'Development', items: ['Xcode 15+', 'iOS 14+'] },
    { title: 'Deployment', items: ['Docker', 'Self-hosted'] }
  ]

  return (
    <section className="py-16 px-6 bg-black">
      <div className="max-w-6xl mx-auto">
        <motion.h3
          className="text-2xl font-bold text-center mb-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Works With Your Stack
        </motion.h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {compat.map((cat, i) => (
            <motion.div
              key={i}
              className="text-center"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <h4 className="text-sm font-semibold text-gray-400 mb-3">{cat.title}</h4>
              <ul className="space-y-2">
                {cat.items.map((item, j) => (
                  <li key={j} className="text-white">✓ {item}</li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Features() {
  const features = [
    { icon: '🧠', title: 'Code-Aware', desc: 'Reads your actual Swift source code to find real accessibility IDs' },
    { icon: '⚡', title: '30-Second Tests', desc: 'Generate tests in seconds, not hours' },
    { icon: '🎯', title: 'Works Out of the Box', desc: 'Supports SwiftUI and UIKit' },
    { icon: '📹', title: 'Visual Proof', desc: 'Every test run is recorded on video' },
    { icon: '🔄', title: 'AI-Enriched', desc: 'Vague descriptions → precise test specifications' },
    { icon: '🗺️', title: 'Navigation Context', desc: "Understands your app's screens and flow" }
  ]

  return (
    <section className="py-20 px-6 bg-gradient-to-b from-black to-gray-900">
      <div className="max-w-6xl mx-auto">
        <motion.h2
          className="text-4xl font-bold text-center mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Everything You Need
        </motion.h2>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={i}
              className="glass p-6 rounded-xl hover:bg-white/10 transition-all"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ y: -5 }}
            >
              <div className="text-3xl mb-3">{feature.icon}</div>
              <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-400 text-sm">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Pricing() {
  return (
    <section className="py-20 px-6 bg-black">
      <div className="max-w-2xl mx-auto">
        <motion.div
          className="glass p-12 rounded-2xl text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl font-bold mb-4">Pilot Program — Free for 3 Months</h2>
          <p className="text-gray-400 mb-8">
            We are onboarding 10 pilot teams to help shape the product.
          </p>

          <ul className="space-y-3 mb-8 text-left max-w-md mx-auto">
            {[
              'Unlimited test generation',
              'Direct support from the founder',
              'Priority feature requests',
              'Your feedback shapes the roadmap'
            ].map((item, i) => (
              <li key={i} className="flex items-center gap-3">
                <span className="text-green-400">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>

          <button className="bg-blue-500 hover:bg-blue-600 text-white px-12 py-4 rounded-full text-lg font-semibold transition-all duration-300 hover:scale-105 mb-4">
            Request Pilot Access
          </button>

          <p className="text-sm text-gray-500 mb-2">
            Setup takes less than 5 minutes. No credit card required.
          </p>
          <p className="text-sm text-gray-400">
            After pilot: $100/month per team
          </p>
        </motion.div>
      </div>
    </section>
  )
}

function FAQ() {
  const faqs = [
    {
      q: 'Is my code safe?',
      a: 'Yes. Testara analyzes your code locally. Your Swift files never leave your machine. Self-hosted deployment available for private repositories.'
    },
    {
      q: 'How accurate are the generated tests?',
      a: '85%+ compile and run on first try. Every test is scored (A-F) so you know quality upfront.'
    },
    {
      q: 'Does it work with SwiftUI and UIKit?',
      a: 'Yes, both are fully supported.'
    },
    {
      q: 'Can I customize the generated code?',
      a: 'Absolutely. Copy it to Xcode and edit as needed. Tests are standard XCUITest code.'
    }
  ]

  return (
    <section className="py-20 px-6 bg-gradient-to-b from-black to-gray-900">
      <div className="max-w-4xl mx-auto">
        <motion.h2
          className="text-4xl font-bold text-center mb-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          FAQ
        </motion.h2>

        <div className="space-y-6">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              className="glass p-6 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <h3 className="text-lg font-bold mb-2">{faq.q}</h3>
              <p className="text-gray-400">{faq.a}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="py-12 px-6 bg-black border-t border-gray-800">
      <div className="max-w-6xl mx-auto text-center text-gray-400">
        <div className="flex items-center justify-center gap-2 mb-4">
          <span className="text-2xl">⚡</span>
          <span className="text-white font-bold text-xl">Testara</span>
        </div>
        <p className="text-sm">
          © 2026 Testara. Built by Mher Yerznkanyan.
        </p>
        <p className="text-sm mt-2">
          AI-Powered iOS Test Generation
        </p>
      </div>
    </footer>
  )
}
