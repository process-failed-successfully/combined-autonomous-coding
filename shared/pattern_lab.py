"""
Design Pattern Lab
==================

Provides templates for common design patterns in multiple languages.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

TEMPLATES: Dict[str, Dict[str, str]] = {
    "Singleton": {
        "python": """class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def some_business_logic(self):
        print("Executing logic...")
""",
        "javascript": """class Singleton {
  constructor() {
    if (Singleton.instance) {
      return Singleton.instance;
    }
    Singleton.instance = this;
  }

  someBusinessLogic() {
    console.log("Executing logic...");
  }
}

module.exports = Singleton;
""",
        "go": """package main

import (
	"sync"
)

type singleton struct{}

var instance *singleton
var once sync.Once

func GetInstance() *singleton {
	once.Do(func() {
		instance = &singleton{}
	})
	return instance
}
"""
    },
    "Factory": {
        "python": """class Product:
    def operation(self):
        pass

class ConcreteProductA(Product):
    def operation(self):
        return "Result of ConcreteProductA"

class ConcreteProductB(Product):
    def operation(self):
        return "Result of ConcreteProductB"

class Creator:
    def factory_method(self):
        pass

    def some_operation(self):
        product = self.factory_method()
        return f"Creator: The same creator's code has just worked with {product.operation()}"

class ConcreteCreatorA(Creator):
    def factory_method(self):
        return ConcreteProductA()

class ConcreteCreatorB(Creator):
    def factory_method(self):
        return ConcreteProductB()
""",
        "javascript": """class Product {
  operation() {}
}

class ConcreteProductA extends Product {
  operation() {
    return "Result of ConcreteProductA";
  }
}

class ConcreteProductB extends Product {
  operation() {
    return "Result of ConcreteProductB";
  }
}

class Creator {
  factoryMethod() {}

  someOperation() {
    const product = this.factoryMethod();
    return `Creator: The same creator's code has just worked with ${product.operation()}`;
  }
}

class ConcreteCreatorA extends Creator {
  factoryMethod() {
    return new ConcreteProductA();
  }
}

class ConcreteCreatorB extends Creator {
  factoryMethod() {
    return new ConcreteProductB();
  }
}
""",
        "go": """package main

import "fmt"

type Product interface {
	Operation() string
}

type ConcreteProductA struct{}

func (p *ConcreteProductA) Operation() string {
	return "Result of ConcreteProductA"
}

type ConcreteProductB struct{}

func (p *ConcreteProductB) Operation() string {
	return "Result of ConcreteProductB"
}

func FactoryMethod(t string) Product {
	if t == "A" {
		return &ConcreteProductA{}
	} else if t == "B" {
		return &ConcreteProductB{}
	}
	return nil
}
"""
    },
    "Observer": {
        "python": """class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)

class Observer:
    def update(self, subject):
        pass

class ConcreteObserverA(Observer):
    def update(self, subject):
        print("ConcreteObserverA: Reacted to the event")

class ConcreteObserverB(Observer):
    def update(self, subject):
        print("ConcreteObserverB: Reacted to the event")
""",
        "javascript": """class Subject {
  constructor() {
    this.observers = [];
  }

  attach(observer) {
    this.observers.push(observer);
  }

  detach(observer) {
    const index = this.observers.indexOf(observer);
    if (index > -1) {
      this.observers.splice(index, 1);
    }
  }

  notify() {
    for (const observer of this.observers) {
      observer.update(this);
    }
  }
}

class Observer {
  update(subject) {}
}

class ConcreteObserverA extends Observer {
  update(subject) {
    console.log("ConcreteObserverA: Reacted to the event");
  }
}
""",
        "go": """package main

import "fmt"

type Observer interface {
	Update(string)
}

type Subject interface {
	Attach(Observer)
	Detach(Observer)
	Notify()
}

type ConcreteSubject struct {
	observers []Observer
	state     string
}

func (s *ConcreteSubject) Attach(o Observer) {
	s.observers = append(s.observers, o)
}

func (s *ConcreteSubject) Notify() {
	for _, o := range s.observers {
		o.Update(s.state)
	}
}
"""
    },
    "Strategy": {
        "python": """from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

class Context:
    def __init__(self, strategy: Strategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        self._strategy = strategy

    def do_some_business_logic(self) -> None:
        print("Context: Sorting data using the strategy (not sure how it'll do it)")
        result = self._strategy.do_algorithm(["a", "b", "c", "d", "e"])
        print(",".join(result))

class Strategy(ABC):
    @abstractmethod
    def do_algorithm(self, data: List) -> List:
        pass

class ConcreteStrategyA(Strategy):
    def do_algorithm(self, data: List) -> List:
        return sorted(data)

class ConcreteStrategyB(Strategy):
    def do_algorithm(self, data: List) -> List:
        return sorted(data, reverse=True)
""",
        "javascript": """class Context {
  constructor(strategy) {
    this.strategy = strategy;
  }

  setStrategy(strategy) {
    this.strategy = strategy;
  }

  doSomeBusinessLogic() {
    const result = this.strategy.doAlgorithm(["a", "b", "c", "d", "e"]);
    console.log(result.join(","));
  }
}

class Strategy {
  doAlgorithm(data) {}
}

class ConcreteStrategyA extends Strategy {
  doAlgorithm(data) {
    return data.sort();
  }
}

class ConcreteStrategyB extends Strategy {
  doAlgorithm(data) {
    return data.sort().reverse();
  }
}
""",
        "go": """package main

import "fmt"

type Strategy interface {
	DoAlgorithm([]string) []string
}

type ConcreteStrategyA struct{}

func (s *ConcreteStrategyA) DoAlgorithm(data []string) []string {
	// sort logic
	return data
}

type ConcreteStrategyB struct{}

func (s *ConcreteStrategyB) DoAlgorithm(data []string) []string {
	// reverse sort logic
	return data
}

type Context struct {
	strategy Strategy
}

func (c *Context) SetStrategy(s Strategy) {
	c.strategy = s
}

func (c *Context) Execute() {
	c.strategy.DoAlgorithm([]string{"a", "b"})
}
"""
    }
}

class PatternLabManager:
    """Manages design pattern templates."""

    def list_patterns(self) -> List[str]:
        """Returns available pattern names."""
        return sorted(TEMPLATES.keys())

    def list_languages(self) -> List[str]:
        """Returns available languages."""
        # Assume all patterns support at least python, but let's gather all unique
        langs = set()
        for p in TEMPLATES.values():
            langs.update(p.keys())
        return sorted(list(langs))

    def get_template(self, pattern: str, language: str) -> Optional[str]:
        """Returns the code for the pattern in the specified language."""
        pat = TEMPLATES.get(pattern)
        if not pat:
            return None
        return pat.get(language.lower())

    def generate(self, pattern: str, language: str, output_path: str) -> bool:
        """Writes the pattern code to a file."""
        code = self.get_template(pattern, language)
        if not code:
            return False

        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
            return True
        except Exception:
            return False

def run_pattern_lab_logic(args):
    """CLI logic for Pattern Lab."""
    manager = PatternLabManager()

    if args.action == "list":
        print("--- Design Patterns ---")
        for p in manager.list_patterns():
            print(f"  - {p}")
        print("\n--- Languages ---")
        for l in manager.list_languages():
            print(f"  - {l}")
        sys.exit(0)

    elif args.action == "show":
        if not args.pattern or not args.lang:
            print("Error: --pattern and --lang are required.", file=sys.stderr)
            sys.exit(1)

        code = manager.get_template(args.pattern, args.lang)
        if code:
            print(code)
        else:
            print(f"Pattern '{args.pattern}' not found for language '{args.lang}'.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "generate":
        if not args.pattern or not args.lang or not args.output:
            print("Error: --pattern, --lang, and --output are required.", file=sys.stderr)
            sys.exit(1)

        if manager.generate(args.pattern, args.lang, args.output):
            print(f"✅ Generated {args.pattern} ({args.lang}) to {args.output}")
        else:
            print(f"❌ Failed to generate pattern.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)
