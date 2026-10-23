import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Concept } from './concept';

const CONCEPTS: Concept[] = [
  // JavaScript
  {
    slug: 'for-of',
    topic: 'javascript',
    subtopic: 'schleifen',
    title: 'for...of-Schleife',
    summary: 'Jedes Element eines Arrays durchlaufen.',
    explanation:
      'for...of nimmt nacheinander jeden Wert aus einem Array und führt den Block in den geschweiften Klammern einmal pro Wert aus. Mit const bekommt jeder Durchlauf eine eigene Variable.',
    language: 'javascript',
    code: "const namen = ['Anna', 'Ben', 'Cem'];\n\nfor (const name of namen) {\n  console.log(`Hallo ${name}`);\n}",
    note: 'for...in durchläuft die Schlüssel, bei Arrays also die Indizes als Text. Für die Werte eines Arrays nimmst du for...of.',
  },
  {
    slug: 'map-foreach',
    topic: 'javascript',
    subtopic: 'arrays',
    title: 'map und forEach',
    summary: 'Mit jedem Element etwas tun oder ein neues Array bauen.',
    explanation:
      'Beide rufen eine Funktion für jedes Element auf. map sammelt die Rückgabewerte in einem neuen Array, das alte bleibt unverändert. forEach gibt nichts zurück und eignet sich für Ausgaben oder Nebenwirkungen.',
    language: 'javascript',
    code: 'const preise = [10, 20, 30];\n\nconst brutto = preise.map((preis) => preis * 1.19);\npreise.forEach((preis) => console.log(preis));',
    note: 'Brauchst du ein Ergebnis, nimm map. Ein forEach mit push in ein leeres Array ist fast immer ein map.',
  },
  {
    slug: 'async-await',
    topic: 'javascript',
    subtopic: 'async',
    title: 'async und await',
    summary: 'Auf eine Antwort warten, ohne die Seite zu blockieren.',
    explanation:
      'Eine async-Funktion gibt immer ein Promise zurück. Mit await wartet sie an dieser Stelle, bis das Promise fertig ist, und arbeitet dann mit dem Ergebnis weiter. Fehler fängst du wie gewohnt mit try und catch.',
    language: 'javascript',
    code: "async function ladeAufgaben() {\n  try {\n    const antwort = await fetch('/api/tasks/');\n    if (!antwort.ok) {\n      throw new Error(`Status ${antwort.status}`);\n    }\n    return await antwort.json();\n  } catch (fehler) {\n    console.error(fehler);\n  }\n}",
    note: 'fetch wirft bei 404 oder 500 keinen Fehler. Prüfe deshalb immer antwort.ok.',
  },

  // TypeScript
  {
    slug: 'interface',
    topic: 'typescript',
    subtopic: 'interfaces',
    title: 'Interface',
    summary: 'Festlegen, welche Felder ein Objekt hat.',
    explanation:
      'Ein Interface beschreibt die Form eines Objekts: welche Felder es gibt und welchen Typ sie haben. Fehlt ein Feld oder hat es den falschen Typ, meldet der Editor das schon beim Schreiben.',
    language: 'typescript',
    code: "interface Task {\n  id: number;\n  title: string;\n  done: boolean;\n  dueDate?: string;\n}\n\nconst task: Task = { id: 1, title: 'Lernen', done: false };",
    note: 'Das ? macht ein Feld optional. Im fertigen JavaScript gibt es keine Interfaces mehr, sie helfen nur beim Entwickeln.',
  },

  // Angular
  {
    slug: 'input-output',
    topic: 'angular',
    subtopic: 'komponenten',
    title: 'input und output',
    summary: 'Daten in eine Komponente geben und Ereignisse zurückmelden.',
    explanation:
      'Die Eltern-Komponente gibt Daten über ein input hinein und hört über ein output auf Ereignisse. Im Template der Eltern sieht das so aus: <app-task-item [title]="task.title" (removed)="remove(task)" />.',
    language: 'typescript',
    code: "import { Component, input, output } from '@angular/core';\n\n@Component({\n  selector: 'app-task-item',\n  templateUrl: './task-item.html',\n})\nexport class TaskItem {\n  readonly title = input.required<string>();\n  readonly removed = output<void>();\n}",
    note: 'Ein input ist ein Signal. Im Template schreibst du deshalb title(), nicht title.',
  },
  {
    slug: 'signal-computed',
    topic: 'angular',
    subtopic: 'signals',
    title: 'signal und computed',
    summary: 'Zustand speichern und davon abgeleitete Werte berechnen.',
    explanation:
      'Ein signal hält einen Wert. Mit set ersetzt du ihn, mit update berechnest du ihn aus dem alten Wert. computed leitet einen Wert aus anderen Signals ab und rechnet automatisch neu, wenn sich einer davon ändert.',
    language: 'typescript',
    code: "import { computed, signal } from '@angular/core';\n\nconst anzahl = signal(0);\nconst doppelt = computed(() => anzahl() * 2);\n\nanzahl.set(5);\nanzahl.update((wert) => wert + 1);\nconsole.log(doppelt()); // 12",
    note: 'Ein Signal liest du mit Klammern: anzahl(). Ohne Klammern bekommst du das Signal selbst, nicht seinen Wert.',
  },

  // Python
  {
    slug: 'for-schleife',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'for-Schleife',
    summary: 'Jedes Element einer Liste durchlaufen.',
    explanation:
      'Die for-Schleife nimmt nacheinander jedes Element aus einer Liste und führt den eingerückten Block einmal pro Element aus. Die Variable nach for enthält dabei das aktuelle Element.',
    language: 'python',
    code: 'namen = ["Anna", "Ben", "Cem"]\n\nfor name in namen:\n    print(f"Hallo {name}")',
    note: 'Was zur Schleife gehört, erkennt Python an der Einrückung. Fehlt sie, gibt es einen IndentationError.',
  },
  {
    slug: 'range',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'Zählen mit range()',
    summary: 'Eine Schleife eine bestimmte Anzahl Male laufen lassen.',
    explanation:
      'range(stop) erzeugt die Zahlen von 0 bis vor stop. Mit range(start, stop, schritt) legst du Anfang und Schrittweite selbst fest.',
    language: 'python',
    code: 'for i in range(5):\n    print(i)  # 0, 1, 2, 3, 4\n\nfor i in range(2, 10, 2):\n    print(i)  # 2, 4, 6, 8',
    note: 'range(5) zählt von 0 bis 4. Die 5 selbst ist nicht dabei.',
  },
  {
    slug: 'while-schleife',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'while-Schleife',
    summary: 'Wiederholen, solange eine Bedingung gilt.',
    explanation:
      'Die while-Schleife prüft vor jedem Durchlauf ihre Bedingung. Ist sie wahr, läuft der Block noch einmal. Sie passt, wenn du vorher nicht weißt, wie oft wiederholt werden muss.',
    language: 'python',
    code: 'versuche = 0\n\nwhile versuche < 3:\n    print(f"Versuch {versuche + 1}")\n    versuche += 1',
    note: 'Wird die Bedingung nie falsch, läuft die Schleife endlos. Im Terminal brichst du mit Strg + C ab.',
  },
  {
    slug: 'break-continue',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'break und continue',
    summary: 'Eine Schleife abbrechen oder einen Durchlauf überspringen.',
    explanation:
      'break beendet die Schleife sofort. continue springt zum nächsten Durchlauf, der Rest des Blocks wird übersprungen.',
    language: 'python',
    code: 'for zahl in [3, 8, -1, 5]:\n    if zahl < 0:\n        break\n    if zahl % 2 == 0:\n        continue\n    print(zahl)  # nur 3',
    note: 'break und continue wirken nur auf die innerste Schleife.',
  },
  {
    slug: 'enumerate',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'Mitzählen mit enumerate()',
    summary: 'Beim Durchlaufen auch die Nummer des Elements bekommen.',
    explanation:
      'enumerate liefert bei jedem Durchlauf zwei Werte: die Nummer und das Element. So brauchst du keinen eigenen Zähler.',
    language: 'python',
    code: 'aufgaben = ["Einkaufen", "Sport", "Lernen"]\n\nfor nummer, aufgabe in enumerate(aufgaben, start=1):\n    print(f"{nummer}. {aufgabe}")',
    note: 'Ohne start beginnt enumerate bei 0.',
  },
  {
    slug: 'liste-aendern',
    topic: 'python',
    subtopic: 'listen',
    title: 'Listen anlegen und ändern',
    summary: 'Mehrere Werte in einer Variable sammeln.',
    explanation:
      'Eine Liste steht in eckigen Klammern. Mit append hängst du ein Element hinten an, mit remove entfernst du eins, len gibt die Anzahl zurück.',
    language: 'python',
    code: 'farben = ["rot", "grün"]\nfarben.append("blau")\nfarben.remove("rot")\n\nprint(farben)       # [\'grün\', \'blau\']\nprint(len(farben))  # 2',
    note: 'remove löscht nur das erste passende Element und wirft einen ValueError, wenn es fehlt.',
  },
  {
    slug: 'index-slicing',
    topic: 'python',
    subtopic: 'listen',
    title: 'Index und Slicing',
    summary: 'Einzelne Elemente oder Ausschnitte einer Liste holen.',
    explanation:
      'Mit einer Zahl in eckigen Klammern holst du ein Element, negative Zahlen zählen von hinten. Mit start:stop bekommst du einen Ausschnitt als neue Liste, stop ist dabei nicht enthalten.',
    language: 'python',
    code: 'zahlen = [10, 20, 30, 40, 50]\n\nprint(zahlen[0])    # 10\nprint(zahlen[-1])   # 50\nprint(zahlen[1:3])  # [20, 30]',
    note: 'Der Index beginnt bei 0. Ein Index außerhalb der Liste führt zu einem IndexError.',
  },
  {
    slug: 'list-comprehension',
    topic: 'python',
    subtopic: 'listen',
    title: 'List Comprehension',
    summary: 'Eine neue Liste in einer Zeile aus einer anderen bauen.',
    explanation:
      'Eine List Comprehension ist eine kurze Schreibweise für eine for-Schleife, die eine neue Liste füllt. Mit if am Ende kommen nur passende Elemente hinein.',
    language: 'python',
    code: 'zahlen = [1, 2, 3, 4, 5]\n\nquadrate = [z * z for z in zahlen]\ngerade = [z for z in zahlen if z % 2 == 0]',
    note: 'Wird die Zeile lang oder verschachtelt, ist eine normale for-Schleife besser lesbar.',
  },
  {
    slug: 'def-return',
    topic: 'python',
    subtopic: 'funktionen',
    title: 'Funktionen mit def und return',
    summary: 'Code einmal schreiben und mit anderen Werten wiederverwenden.',
    explanation:
      'Mit def legst du eine Funktion an. Die Werte in den Klammern heißen Parameter, ein Parameter mit = hat einen Standardwert. return gibt das Ergebnis an die Stelle zurück, an der die Funktion aufgerufen wurde.',
    language: 'python',
    code: 'def brutto(netto, steuer=0.19):\n    return round(netto * (1 + steuer), 2)\n\nprint(brutto(100))        # 119.0\nprint(brutto(100, 0.07))  # 107.0',
    note: 'Ohne return gibt eine Funktion None zurück.',
  },

  // Django
  {
    slug: 'model-definieren',
    topic: 'django',
    subtopic: 'models-migrationen',
    title: 'Model definieren',
    summary: 'Eine Datenbanktabelle als Python-Klasse beschreiben.',
    explanation:
      'Jede Klasse, die von models.Model erbt, wird zu einer Tabelle. Jedes Feld der Klasse wird zu einer Spalte. Django legt die Spalte id automatisch an.',
    language: 'python',
    code: 'from django.db import models\n\n\nclass Task(models.Model):\n    title = models.CharField(max_length=200)\n    done = models.BooleanField(default=False)\n    created_at = models.DateTimeField(auto_now_add=True)',
    note: 'Nach jeder Änderung am Model: python manage.py makemigrations und danach python manage.py migrate.',
  },

  // Django REST Framework
  {
    slug: 'model-serializer',
    topic: 'django-rest-framework',
    subtopic: 'serializer',
    title: 'ModelSerializer',
    summary: 'Ein Model in JSON umwandeln und eingehende Daten prüfen.',
    explanation:
      'Ein ModelSerializer baut die Felder aus deinem Model selbst auf. In der inneren Klasse Meta legst du fest, welches Model und welche Felder er verwendet.',
    language: 'python',
    code: "from rest_framework import serializers\n\nfrom .models import Task\n\n\nclass TaskSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = Task\n        fields = ['id', 'title', 'done', 'created_at']\n        read_only_fields = ['created_at']",
    note: "fields = '__all__' gibt auch Felder heraus, die du vielleicht nicht zeigen willst. Nenne die Felder lieber einzeln.",
  },

  // Git
  {
    slug: 'branch-anlegen',
    topic: 'git',
    subtopic: 'branches',
    title: 'Mit einem Branch arbeiten',
    summary: 'An einem Feature arbeiten, ohne main zu verändern.',
    explanation:
      'Ein Branch ist ein eigener Entwicklungszweig. Du legst ihn an, speicherst dort deine Commits und schickst ihn zu GitHub. Über einen Pull Request kommt er später in main.',
    language: 'terminal',
    code: 'git switch -c feat/login\ngit add .\ngit commit -m "feat: add login form"\ngit push -u origin feat/login',
    note: 'Wechsle vor dem neuen Branch auf main und führe git pull aus, sonst fehlen dir neue Änderungen.',
  },
];

@Service()
export class ConceptApi {
  getByTopic(topic: string): Observable<Concept[]> {
    return of(CONCEPTS.filter((concept) => concept.topic === topic));
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return of({
      entries: CONCEPTS.length,
      topics: new Set(CONCEPTS.map((concept) => concept.topic)).size,
    });
  }
}
