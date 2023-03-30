// import blocks
import Header from "./header";
import Paragraph from "./paragraph";
import Card from "./card";
import Chart from "./chart";
import Shortcut from "./shortcut";
import Spacer from "./spacer";
import Onboarding from "./onboarding";
import QuickList from "./quick_list";
import NumberCard from "./number_card";

// import tunes
import HeaderSize from "./header_size";

dontmanage.provide("dontmanage.workspace_block");

dontmanage.workspace_block.blocks = {
	header: Header,
	paragraph: Paragraph,
	card: Card,
	chart: Chart,
	shortcut: Shortcut,
	spacer: Spacer,
	onboarding: Onboarding,
	quick_list: QuickList,
	number_card: NumberCard,
};

dontmanage.workspace_block.tunes = {
	header_size: HeaderSize,
};
