import { writeFileSync, readFileSync } from "fs";
import {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    HeadingLevel, AlignmentType, WidthType, BorderStyle, ShadingType, PageBreak, LevelFormat,
    ImageRun
} from "docx";
import { join } from "path";

const FONT = "Liberation Serif";

/**
 * Reusable Report Engine for AgriTech Project Reports
 */
export class ReportEngine {
    constructor(author = "Цар Ю.А.", group = "ФеІ-36", reviewer = "доц. Ляшкевич В. Я.") {
        this.author = author;
        this.group = group;
        this.reviewer = reviewer;
    }

    createTitlePage(stepNumber, topicTitle) {
        const emptyLines = (count) => Array.from({ length: count }).map(() => new Paragraph({ children: [new TextRun("")] }));

        return [
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Міністерство освіти та науки україни", font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Львівський Університет імені Івана Франка", font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Факультет електроніки та комп’ютерних технологій", font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Кафедра системного проектування", font: FONT, size: 28 })]
            }),
            ...emptyLines(10),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Звіт", font: FONT, size: 36 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: `до Проектного завдання №${stepNumber}`, font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: `«${topicTitle}»`, font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "з предмету «Проєкт з розробки системи опрацювання даних»", font: FONT, size: 28 })]
            }),
            ...emptyLines(10),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "Виконав", font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: `студент групи ${this.group}`, font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: this.author, font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: "перевірив", font: FONT, size: 28 })]
            }),
            new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [new TextRun({ text: this.reviewer, font: FONT, size: 28 })]
            }),
            ...emptyLines(14),
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun({ text: "Львів — 2026", font: FONT, size: 28 })]
            }),
            new Paragraph({ children: [new PageBreak()] })
        ];
    }

    createHeading(text, level) {
        return new Paragraph({
            heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
            alignment: AlignmentType.LEFT,
            spacing: { before: 240, after: 120 },
            children: [new TextRun({ text: text, font: FONT, size: level === 1 ? 32 : 28, bold: true })]
        });
    }

    createParagraph(text) {
        return new Paragraph({
            spacing: { before: 120, after: 120 },
            children: [new TextRun({ text: text, font: FONT, size: 24 })]
        });
    }

    createBulletPoint(text) {
        return new Paragraph({
            numbering: { reference: "bullets", level: 0 },
            spacing: { before: 60, after: 60 },
            children: [new TextRun({ text: text, font: FONT, size: 24 })]
        });
    }

    createTableCell(text, isHeader = false) {
        return new TableCell({
            children: [new Paragraph({
                children: [new TextRun({ text: text, font: FONT, size: isHeader ? 22 : 20, bold: isHeader })],
                alignment: AlignmentType.CENTER
            })],
            shading: isHeader ? { fill: "E7E6E6", type: ShadingType.CLEAR } : undefined,
            verticalAlign: AlignmentType.CENTER
        });
    }

    createTable(rowsData, options = {}) {
        const { firstRowHeader = true, firstColHeader = false } = options;
        return new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            borders: {
                top: { style: BorderStyle.SINGLE, size: 1 },
                bottom: { style: BorderStyle.SINGLE, size: 1 },
                left: { style: BorderStyle.SINGLE, size: 1 },
                right: { style: BorderStyle.SINGLE, size: 1 },
                insideHorizontal: { style: BorderStyle.SINGLE, size: 1 },
                insideVertical: { style: BorderStyle.SINGLE, size: 1 },
            },
            rows: rowsData.map((rowData, rowIndex) => new TableRow({
                children: rowData.map((cellText, colIndex) => {
                    const isHeader = (firstRowHeader && rowIndex === 0) || (firstColHeader && colIndex === 0);
                    return this.createTableCell(cellText, isHeader);
                })
            }))
        });
    }

    createImage(path, width = 450, height = 300, caption = "") {
        const paragraphs = [
            new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                    new ImageRun({
                        data: readFileSync(path),
                        transformation: { width, height },
                        type: path.split('.').pop().toLowerCase() === 'png' ? 'png' : 'jpg'
                    })
                ]
            })
        ];

        if (caption) {
            paragraphs.push(new Paragraph({
                alignment: AlignmentType.CENTER,
                spacing: { before: 120, after: 240 },
                children: [new TextRun({ text: caption, font: FONT, size: 20, italic: true })]
            }));
        }

        return paragraphs;
    }

    async generate(config, outputPath) {
        const { stepNumber, topic, objective, body, results, conclusions } = config;

        const children = [
            ...this.createTitlePage(stepNumber, topic),
            this.createHeading("Мета", 1),
            this.createParagraph(objective),
            this.createHeading("Хід роботи", 1),
        ];

        body.forEach(item => {
            if (item.type === 'heading') {
                children.push(this.createHeading(item.text, item.level || 2));
            } else if (item.type === 'text') {
                children.push(this.createParagraph(item.text));
            } else if (item.type === 'list') {
                item.items.forEach(bullet => children.push(this.createBulletPoint(bullet)));
            } else if (item.type === 'table') {
                children.push(this.createTable(item.data, item.options || {}));
            } else if (item.type === 'image') {
                const imgParagraphs = this.createImage(item.path, item.width, item.height, item.caption);
                children.push(...imgParagraphs);
            }
        });

        children.push(this.createHeading("Результати", 1));
        children.push(this.createParagraph(results));
        children.push(this.createHeading("Висновки", 1));
        children.push(this.createParagraph(conclusions));

        const doc = new Document({
            styles: {
                default: { document: { run: { font: FONT, size: 24 } } },
                paragraphStyles: [
                    {
                        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
                        run: { size: 32, bold: true, font: FONT },
                        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0, alignment: AlignmentType.LEFT }
                    },
                    {
                        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
                        run: { size: 28, bold: true, font: FONT },
                        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
                    },
                ]
            },
            numbering: {
                config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "-", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }]
            },
            sections: [{
                properties: {
                    page: {
                        size: { width: 11906, height: 16838 },
                        margin: { top: 1134, right: 1000, bottom: 1134, left: 1000 }
                    }
                },
                children
            }]
        });

        const buffer = await Packer.toBuffer(doc);
        const fileName = join(outputPath, `Цар_Проект_Тиж_${stepNumber}.docx`);
        writeFileSync(fileName, buffer);
        console.log(`Generated: ${fileName}`);
    }
}
