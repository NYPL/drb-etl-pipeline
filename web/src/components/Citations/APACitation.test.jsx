// /* eslint-disable react/jsx-filename-extension */
// /* eslint-env mocha */
// import React from "react";
// // @ts-expect-error ts-migrate(2307) FIXME: Cannot find module 'chai' or its corresponding typ... Remove this comment to see the full error message
// import { expect } from "chai";
// // @ts-expect-error ts-migrate(2307) FIXME: Cannot find module 'sinon' or its corresponding ty... Remove this comment to see the full error message
// import { stub } from "~/src/__tests__/helpers/node_modules/sinon";
// // @ts-expect-error ts-migrate(2307) FIXME: Cannot find module 'enzyme' or its corresponding t... Remove this comment to see the full error message
// import { mount, configure } from "~/src/__tests__/unit/node_modules/enzyme";
// // @ts-expect-error ts-migrate(2307) FIXME: Cannot find module 'enzyme-adapter-react-16' or it... Remove this comment to see the full error message
// import Adapter from "~/src/__tests__/unit/node_modules/enzyme-adapter-react-16";
// // @ts-expect-error ts-migrate(2307) FIXME: Cannot find module '../../src/app/components/Citat... Remove this comment to see the full error message
// import APACitation from "../../src/app/components/Citations/APACitation";

// configure({ adapter: new Adapter() });

// // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
// describe("APA Citation", () => {
//   // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
//   describe("getInitials", () => {
//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should transform names into initials", () => {
//       expect(APACitation.getInitials("Test name")).to.equal("T. N.");
//     });
//   });

//   // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
//   describe("formatCitationData()", () => {
//     let component;
//     let instance: any;
//     let stubFormatNames: any;
//     // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'before'.
//     before(() => {
//       stubFormatNames = stub(APACitation.prototype, "formatAgentNames").returns(
//         "Agent, T."
//       );
//       component = mount(
//         <APACitation
//           title="Testing"
//           subTitle="subTest"
//           agents={{
//             authors: ["author1", "author2"],
//             editors: ["editor1"],
//             translators: ["trans1"],
//             illustrators: ["illus1"],
//             publishers: ["publisher1", "publisher2"],
//           }}
//           publicationYear="2020"
//           edition="Test Edition"
//           volume="Test Volume"
//           sourceLink="test_link"
//           isGovernmentDoc={false}
//         />
//       );
//       instance = component.instance();
//     });

//     // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'after'.
//     after(() => {
//       stubFormatNames.restore();
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should assign title and subtitle to title", () => {
//       instance.formatCitationData();
//       expect(instance.title).to.equal("Testing: subTest");
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should set output from formatAgentNames to all agent names", () => {
//       instance.formatCitationData();
//       expect(instance.authors).to.equal("Agent, T.");
//       expect(instance.editors).to.equal("Agent, T., (Ed.)");
//       expect(instance.translators).to.equal("Agent, T., Trans.");
//       expect(instance.illustrators).to.equal("Agent, T., Illus.");
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should set publication/publisher fields", () => {
//       instance.formatCitationData();
//       expect(instance.pubYear).to.equal(" (2020)");
//       expect(instance.publishers).to.equal("publisher1, publisher2");
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should set edition/volume fields", () => {
//       instance.formatCitationData();
//       expect(instance.volume).to.equal(" (Test Volume)");
//       expect(instance.edition).to.equal(" (Test Edition)");
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should set link as an <a> element", () => {
//       instance.formatCitationData();
//       const linkElem = mount(<span>{instance.link}</span>);
//       expect(linkElem.find("a").text()).to.equal("test_link");
//       expect(linkElem.find("a").prop("href")).to.equal("https://test_link");
//     });
//   });

//   // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
//   describe("formatAgentNames()", () => {
//     let component;
//     let instance: any;
//     const testAgents = {
//       testing: ["Test, Agent", "Other Test", "Test, Some Names", "S. A. Test"],
//     };
//     let stubFormatData: any;
//     let stubReturnMonograph: any;

//     // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'before'.
//     before(() => {
//       stubFormatData = stub(APACitation.prototype, "formatCitationData");
//       stubReturnMonograph = stub(
//         APACitation.prototype,
//         "returnMonographCitation"
//       ).returns("Testing");
//       component = mount(<APACitation agents={testAgents} />);
//       instance = component.instance();
//     });

//     // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'after'.
//     after(() => {
//       stubFormatData.restore();
//       stubReturnMonograph.restore();
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should turn names into a comma-delimited list of initialized names", () => {
//       const agentNames = instance.formatAgentNames("testing");
//       expect(agentNames).to.equal(
//         "Test, A., Test, O., Test, S. N., Test, S. A."
//       );
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should turn names into a comma-delimited list of initialized names, with initial first", () => {
//       const agentNames = instance.formatAgentNames("testing", true);
//       expect(agentNames).to.equal("A. Test, O. Test, S. N. Test, S. A. Test");
//     });
//   });

//   // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
//   describe("returnMonographCitation()", () => {
//     let component;
//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should return formatted monograph citation", () => {
//       component = mount(
//         <APACitation
//           title="Testing"
//           subTitle="subTest"
//           agents={{
//             authors: ["Author, Test"],
//             editors: ["Editor, Test"],
//             translators: ["Translator, Test"],
//             illustrators: ["Illustrator, Test"],
//             publishers: ["Test Publisher"],
//           }}
//           publicationYear="2020"
//           edition="Test Edition"
//           volume={null}
//           sourceLink="test_link"
//           isGovernmentDoc={false}
//         />
//       );
//       const citationText = component.find(".apa-citation").text();
//       const outText =
//         "APAAuthor, T. (2020). Testing: subTest (T. Illustrator, Illus., T. Translator, Trans.) " +
//         "(Test Edition) (T. Editor, (Ed.)). Test Publisher. test_link";
//       expect(citationText).to.equal(outText);
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should return formatted monograph citation with editors if no authors", () => {
//       component = mount(
//         <APACitation
//           title="Testing"
//           subTitle="subTest"
//           agents={{
//             authors: [],
//             editors: ["Editor, Test"],
//             translators: ["Translator, Test"],
//             illustrators: [],
//             publishers: ["Test Publisher"],
//           }}
//           publicationYear="2020"
//           edition="Test Edition"
//           sourceLink="test_link"
//           isGovernmentDoc={false}
//         />
//       );
//       const citationText = component.find(".apa-citation").text();
//       const outText =
//         "APAEditor, T., (Ed.) (2020). Testing: subTest (T. Translator, Trans.) (Test Edition) Test Publisher. test_link";
//       expect(citationText).to.equal(outText);
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//     it("should return formatted monograph citation with volume if included", () => {
//       component = mount(
//         <APACitation
//           title="Testing"
//           subTitle="subTest"
//           agents={{
//             authors: ["Author, Test"],
//             editors: [],
//             translators: [],
//             illustrators: [],
//             publishers: ["Test Publisher"],
//           }}
//           publicationYear="2020"
//           volume="Vol. 2"
//           sourceLink="test_link"
//           isGovernmentDoc={false}
//         />
//       );
//       const citationText = component.find(".apa-citation").text();
//       const outText =
//         "APAAuthor, T. (2020). Testing: subTest (Vol. 2) Test Publisher. test_link";
//       expect(citationText).to.equal(outText);
//     });

//     // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'describe'. Do you need to instal... Remove this comment to see the full error message
//     describe("returnGovernmentReport()", () => {
//       // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//       it("should return formattedw report citation", () => {
//         component = mount(
//           <APACitation
//             title="Testing"
//             subTitle="subTest"
//             agents={{
//               authors: ["Author, Test"],
//               editors: ["Editor, Test"],
//               translators: ["Translator, Test"],
//               illustrators: ["Illustrator, Test"],
//               publishers: ["Test Publisher"],
//             }}
//             publicationYear="2020"
//             edition="Test Edition"
//             sourceLink="test_link"
//             isGovernmentDoc
//           />
//         );
//         const citationText = component.find(".apa-citation").text();
//         const outText =
//           "APAAuthor, T. (2020). Testing: subTest Test Publisher. test_link";
//         expect(citationText).to.equal(outText);
//       });

//       // @ts-expect-error ts-migrate(2582) FIXME: Cannot find name 'it'. Do you need to install type... Remove this comment to see the full error message
//       it("should return formatted report citation with editors if no authors", () => {
//         component = mount(
//           <APACitation
//             title="Testing"
//             subTitle="subTest"
//             agents={{
//               authors: [],
//               editors: ["Editor, Test"],
//               translators: ["Translator, Test"],
//               illustrators: [],
//               publishers: ["Test Publisher"],
//             }}
//             publicationYear="2020"
//             edition="Test Edition"
//             sourceLink="test_link"
//             isGovernmentDoc
//           />
//         );
//         const citationText = component.find(".apa-citation").text();
//         const outText =
//           "APAEditor, T., (Ed.) (2020). Testing: subTest Test Publisher. test_link";
//         expect(citationText).to.equal(outText);
//       });
//     });
//   });
// });
