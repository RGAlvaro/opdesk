// Parse release changelog Markdown into renderable frontend entries.

export type ChangelogSectionName = "Added" | "Changed" | "Fixed";

export type ChangelogEntry = {
  heading: string;
  sections: Array<{
    name: ChangelogSectionName;
    items: string[];
  }>;
};

const entryPattern = /^## (?<heading>\d{4}-\d{2}-\d{2} - .+)$/;
const sectionPattern = /^### (?<section>Added|Changed|Fixed)$/;

/** Convert the repository changelog format into structured page data. */
export function parseChangelog(markdown: string): ChangelogEntry[] {
  const entries: ChangelogEntry[] = [];
  let currentEntry: ChangelogEntry | null = null;
  let currentSection: ChangelogEntry["sections"][number] | null = null;

  for (const line of markdown.split("\n")) {
    const entryMatch = entryPattern.exec(line);
    if (entryMatch?.groups?.heading) {
      currentEntry = { heading: entryMatch.groups.heading, sections: [] };
      entries.push(currentEntry);
      currentSection = null;
      continue;
    }

    const sectionMatch = sectionPattern.exec(line);
    if (sectionMatch?.groups?.section && currentEntry) {
      currentSection = {
        name: sectionMatch.groups.section as ChangelogSectionName,
        items: [],
      };
      currentEntry.sections.push(currentSection);
      continue;
    }

    if (line.startsWith("- ") && currentSection) {
      currentSection.items.push(line.slice(2));
    }
  }

  return entries.filter((entry) =>
    entry.sections.some((section) => section.items.length > 0),
  );
}
