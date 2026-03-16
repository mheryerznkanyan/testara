//
//  AccessibilityIdentificable.swift
//
//  Created by Michal Zaborowski on 2021-03-13.
//  Copyright (c) 2021 Michał Zaborowski. All rights reserved.
//
//  Permission is hereby granted, free of charge, to any person obtaining a copy
//  of this software and associated documentation files (the "Software"), to deal
//  in the Software without restriction, including without limitation the rights
//  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//  copies of the Software, and to permit persons to whom the Software is
//  furnished to do so, subject to the following conditions:
//
//  The above copyright notice and this permission notice shall be included in
//  all copies or substantial portions of the Software.
//
//  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
//  THE SOFTWARE.

import UIKit

@objc
protocol AccessibilityIdentificable: Swizzlable {}

extension AccessibilityIdentificable {
    func generateAccessibilityIdentifiers() {
        let mirror = Mirror(reflecting: self)
        for child in mirror.children {
            guard let identifier = child.label?.replacingOccurrences(of: ".storage", with: "")
                .replacingOccurrences(of: "$__lazy_storage_$_", with: ""), identifier != "delegate" else {
                continue
            }
            if let view = child.value as? UIView {
                view.accessibilityIdentifier = "\(type(of: self)).\(identifier)"
            } else if let array = child.value as? [UIView] {
                for (index, object) in array.enumerated() {
                    object.accessibilityIdentifier = "\(type(of: self)).\(identifier)_\(index)"
                }
            }
        }
        guard let view = self as? UIView else { return }
        guard view.accessibilityIdentifier.isNil else { return }
        var identifier = "\(type(of: self))"
        if identifier.hasPrefix("_") {
            return
        }
        if let view = self as? UITextField {
            if let view = (view as? AppTextField) {
                if let text = view.leftText {
                    identifier += ".\(text)"
                } else if let text = view.placeholder {
                    identifier += ".\(text)"
                } else if let text = view.supportingText {
                    identifier += ".\(text)"
                }
            } else if let text = view.placeholder {
                identifier += ".\(text)"
            }
        } else if let view = (self as? AppTextView) {
            if let text = view.placeholder {
                identifier += ".\(text)"
            } else if let text = view.supportingText {
                identifier += ".\(text)"
            }
        } else if let label = (self as? UILabel) {
            if let textField = label.superview as? AppTextField, let id = textField.accessibilityIdentifier {
                identifier = "\(id).\(identifier)"
                if textField.leftText == label.text {
                    identifier += ".floatingPlaceholder"
                } else if textField.supportingText == label.text {
                    identifier += ".supportingText"
                }
            } else if let text = label.text, text.isNotEmpty {
                identifier += ".\(text)"
            } else if let text = label.attributedText?.string, text.isNotEmpty {
                identifier += ".\(text)"
            }
        } else if let button = (self as? UIButton) {
            if let text = button.titleLabel?.text, text.isNotEmpty {
                identifier += ".\(text)"
            } else if let name = button.imageView?.image?.name {
                identifier += ".\(name)"
            }
        } else if let view = (self as? UICollectionView) {
            if let direction = (view.collectionViewLayout as? UICollectionViewFlowLayout)?.scrollDirection {
                identifier += ".\(direction)"
            } else if let direction = (view.collectionViewLayout as? UICollectionViewCompositionalLayout)?.configuration.scrollDirection {
                identifier += ".\(direction)"
            }
        } else if let text = (self as? UIImageView)?.image?.name {
            identifier += ".\(text)"
        }
        view.accessibilityIdentifier = "\(type(of: view.parentContainerViewController() ?? view)).\(identifier)".replacingOccurrences(of: " ", with: "_")

        if view is UITableViewCell || view is UICollectionViewCell || view is UISwitch {
            view.isAccessibilityElement = true
        }
        #if QA
            po(view.accessibilityIdentifier)
        #endif
    }
}

extension UIView: AccessibilityIdentificable {
    static func swizzling() {
        changeFunc(.init(classType: UIView.self, selector: #selector(UIView.didMoveToWindow)),
                   with: .init(classType: UIView.self, selector: #selector(overrideDidMoveToWindow)))
    }

    @objc
    private func overrideDidMoveToWindow() {
        overrideDidMoveToWindow()
        generateAccessibilityIdentifiers()
    }
}

extension UIViewController: AccessibilityIdentificable {
    static func swizzling() {
        changeFunc(.init(classType: UIViewController.self, selector: #selector(viewDidLoad)),
                   with: .init(classType: UIViewController.self, selector: #selector(overrideViewDidLoad)))
    }

    @objc
    private func overrideViewDidLoad() {
        overrideViewDidLoad()
        generateAccessibilityIdentifiers()
    }
}
