<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { accountApi } from '../services/accountApi'
import bunnyAvatar from '../assets/avatars/bunny.png'
import flowerAvatar from '../assets/avatars/flower.png'
import koalaAvatar from '../assets/avatars/koala.png'
import sproutAvatar from '../assets/avatars/sprout.png'
import ParentDashboard from '../components/ParentDashboard.vue'
import wordHouse from '../assets/words/house.png'
import wordWater from '../assets/words/water.png'
import wordMango from '../assets/words/mango.png'
import wordTea from '../assets/words/tea.png'
import wordName from '../assets/words/name.png'
import wordFather from '../assets/words/father.png'
import wordRice from '../assets/words/rice.png'
import wordMother from '../assets/words/mother.png'
import wordFish from '../assets/words/fish.png'
import wordBird from '../assets/words/bird.png'
import wordFlower from '../assets/words/flower.png'
import wordBook from '../assets/words/book.png'

const page = ref('login'), flow = ref('login'), error = ref(''), notice = ref('')
const email = ref(''), password = ref(''), confirm = ref(''), code = ref('')
const fieldErrors = ref({})
const busy = ref(false), booting = ref(true), challenge = ref(null), signedIn = ref(null)
const children = ref([]), childrenLoading = ref(false)
const studentHome = ref(null)
const quizCatalog = ref([])
const quizData = ref(null), quizLesson = ref(null), quizAnswers = ref({})
const quizResult = ref(null), quizHistory = ref([])
const learningPreview = ref('')
const studentLesson = ref('home')
const currentWordIndex = ref(0)
const wordFeedback = ref('')
const currentNumberIndex = ref(0)
const currentConversationChapterIndex = ref(0)
const currentConversationIndex = ref(0)
const flippedConversationLines = ref([])
const vowelFeedback = ref('')
const currentVowelIndex = ref(0)
const consonantFeedback = ref('')
const currentConsonantIndex = ref(0)
const currentConsonantVowelIndex = ref(0)
const completedLesson = ref('')
let lessonCompletionTimer
const developmentCodes = ref(false), now = ref(Date.now()), heading = ref(null)
const childNickname = ref(''), childAgeBand = ref('junior'), selectedAvatar = ref('sprout')
const editingChildId = ref(null)
const deleteConfirmId = ref(null)
const deleteChallenge = ref(null), deleteCode = ref('')
const pinEditorOpen = ref(false), parentPin = ref(''), confirmParentPin = ref('')
const parentAccessPin = ref('')
const customAvatarUrl = ref(''), customAvatarName = ref('')
const customAvatarFile = ref(null), existingCustomAvatar = ref('')
const avatarSources = { sprout: sproutAvatar, bunny: bunnyAvatar, koala: koalaAvatar, flower: flowerAvatar }
const avatarChoices = [
  { id: 'sprout', label: 'Sprout', src: sproutAvatar },
  { id: 'bunny', label: 'Bunny', src: bunnyAvatar },
  { id: 'koala', label: 'Koala', src: koalaAvatar },
  { id: 'flower', label: 'Flower', src: flowerAvatar },
]
const learningAreas = [
  {
    id: 'vowels',
    title: 'Vowels',
    label: 'Letters & sounds',
    description: 'Meet the Bangla vowels and practise how each one sounds.',
    symbol: 'অ আ',
    tone: 'mint',
  },
  {
    id: 'consonants',
    title: 'Consonants',
    label: 'Letters & sounds',
    description: 'Explore consonant shapes, sounds, and simple examples.',
    symbol: 'ক খ',
    tone: 'sun',
  },
  {
    id: 'spelling',
    title: 'Spelling & words',
    label: 'Build words',
    description: 'Build useful words and learn the Bangla digits from ০ to ৯.',
    symbol: 'শব্দ',
    tone: 'sky',
  },
  {
    id: 'conversation',
    title: 'Reading & conversations',
    label: 'Read & speak',
    description: 'Follow textbook conversations and read short Bangla stories.',
    symbol: 'পাঠ',
    tone: 'peach',
  },
]
const vowels = [
  {
    letter: 'অ', ipa: '[ɔ]', romanisation: 'a',
    tipTitle: 'Use a short, rounded vowel sound',
    tip: 'Use the open-mid back rounded vowel [ɔ]. It is similar to the vowel in some pronunciations of English “thought”, but keep it short and pure.',
  },
  {
    letter: 'আ', ipa: '[a]', romanisation: 'ā',
    tipTitle: 'Use a broad “a” sound',
    tip: 'Open your mouth and keep the tongue low for [a]. It is similar to the broad vowel in “father”, without adding an English-style glide.',
  },
  {
    letter: 'ই', ipa: '[i]', romanisation: 'i',
    tipTitle: 'Listen for “ee” or a shorter “e”',
    tip: 'Use the close front unrounded vowel [i], similar to the vowel in “see”. Keep the front of your tongue high.',
  },
  {
    letter: 'ঈ', ipa: '[i]', romanisation: 'ī',
    tipTitle: 'Use a clear “ee” sound',
    tip: 'It is close to the vowel in “see”. Keep the front of your tongue high and your lips gently spread.',
  },
  {
    letter: 'উ', ipa: '[u]', romanisation: 'u',
    tipTitle: 'Listen for “oo” or a rounded “o”',
    tip: 'Use the close back rounded vowel [u], similar to the vowel in “food”. Keep the lips rounded and the sound steady.',
  },
  {
    letter: 'ঊ', ipa: '[u]', romanisation: 'ū',
    tipTitle: 'Use a rounded “oo” sound',
    tip: 'It is close to the vowel in “pool”. Round your lips gently and keep the sound smooth and clear.',
  },
  {
    letter: 'ঋ', ipa: '[ri]', romanisation: 'ṛ',
    tipTitle: 'Blend “r” and “ee” smoothly',
    tip: 'Say a light “r” followed immediately by the “ee” in “see”. Keep them together as one smooth syllable: “ri”.',
  },
  {
    letter: 'এ', ipa: '[e, æ]', romanisation: 'e',
    tipTitle: 'Listen for two common values',
    tip: 'Depending on the word, এ can sound like the vowel in “eight” or the “a” in “at”. Learn the exact value together with each word.',
  },
  {
    letter: 'ঐ', ipa: '[oi̯]', romanisation: 'ai',
    tipTitle: 'Glide through an “oy” sound',
    tip: 'Begin with an open “o” and glide quickly toward “ee”, similar to the vowel sound in “boy”.',
  },
  {
    letter: 'ও', ipa: '[o]', romanisation: 'o',
    tipTitle: 'Make a pure rounded “o”',
    tip: 'It is close to the vowel in “go”, but keep it smooth and steady. Avoid adding a strong English-style glide at the end.',
  },
  {
    letter: 'ঔ', ipa: '[ou̯]', romanisation: 'au',
    tipTitle: 'Glide gently through an “ow” sound',
    tip: 'Start with [o] and glide smoothly toward a short non-syllabic [u̯]. Keep both parts within one syllable.',
  },
]
const consonantVowels = [
  { vowel: 'অ', sign: '', signName: 'No sign', ipa: 'ɔ', romanisation: 'ô' },
  { vowel: 'আ', sign: 'া', signName: 'আ-কার', ipa: 'a', romanisation: 'a' },
  { vowel: 'ই', sign: 'ি', signName: 'ই-কার', ipa: 'i', romanisation: 'i' },
  { vowel: 'ঈ', sign: 'ী', signName: 'ঈ-কার', ipa: 'i', romanisation: 'ī' },
  { vowel: 'উ', sign: 'ু', signName: 'উ-কার', ipa: 'u', romanisation: 'u' },
  { vowel: 'ঊ', sign: 'ূ', signName: 'ঊ-কার', ipa: 'u', romanisation: 'ū' },
  { vowel: 'ঋ', sign: 'ৃ', signName: 'ঋ-কার', ipa: 'ri', romanisation: 'ri' },
  { vowel: 'এ', sign: 'ে', signName: 'এ-কার', ipa: 'e', romanisation: 'e' },
  { vowel: 'ঐ', sign: 'ৈ', signName: 'ঐ-কার', ipa: 'oi̯', romanisation: 'oi' },
  { vowel: 'ও', sign: 'ো', signName: 'ও-কার', ipa: 'o', romanisation: 'o' },
  { vowel: 'ঔ', sign: 'ৌ', signName: 'ঔ-কার', ipa: 'ou̯', romanisation: 'ou' },
]
const wordBlendingItems = [
  { id: 'ghor', word: 'ঘর', parts: 'ঘ + র', ipa: '[ɡʱɔr]', romanisation: 'ghôr', meaning: 'house', group: 'অ /ɔ/ · built-in vowel', illustration: wordHouse },
  { id: 'jal', word: 'জল', parts: 'জ + ল', ipa: '[ɟɔl]', romanisation: 'jôl', meaning: 'water', group: 'অ /ɔ/ · built-in vowel', illustration: wordWater },
  { id: 'aam', word: 'আম', parts: 'আ + ম', ipa: '[am]', romanisation: 'am', meaning: 'mango', group: 'আ /a/ · independent vowel', illustration: wordMango },
  { id: 'cha', word: 'চা', parts: 'চ + আ-কার', ipa: '[ca]', romanisation: 'cha', meaning: 'tea', group: 'আ /a/ · vowel sign', illustration: wordTea },
  { id: 'naam', word: 'নাম', parts: 'না + ম', ipa: '[nam]', romanisation: 'nam', meaning: 'name', group: 'আ /a/ · vowel sign', illustration: wordName },
  { id: 'baba', word: 'বাবা', parts: 'বা + বা', ipa: '[baba]', romanisation: 'baba', meaning: 'father', group: 'আ /a/ · vowel sign', illustration: wordFather },
  { id: 'bhat', word: 'ভাত', parts: 'ভা + ত', ipa: '[bʱat̪]', romanisation: 'bhat', meaning: 'rice', group: 'আ /a/ · vowel sign', illustration: wordRice },
  { id: 'ma', word: 'মা', parts: 'ম + আ-কার', ipa: '[ma]', romanisation: 'ma', meaning: 'mother', group: 'আ /a/ · vowel sign', illustration: wordMother },
  { id: 'machh', word: 'মাছ', parts: 'মা + ছ', ipa: '[macʰ]', romanisation: 'machh', meaning: 'fish', group: 'আ /a/ · vowel sign', illustration: wordFish },
  { id: 'pakhi', word: 'পাখি', parts: 'পা + খি', ipa: '[pakʰi]', romanisation: 'pakhi', meaning: 'bird', group: 'ই /i/ · vowel sign', illustration: wordBird },
  { id: 'phul', word: 'ফুল', parts: 'ফু + ল', ipa: '[pʰul]', romanisation: 'phul', meaning: 'flower', group: 'উ /u/ · vowel sign', illustration: wordFlower },
  { id: 'boi', word: 'বই', parts: 'ব + ই', ipa: '[boi̯]', romanisation: 'boi', meaning: 'book', group: 'ঐ /oi̯/ · vowel glide', illustration: wordBook },
]
const numberItems = [
  { digit: '০', value: 0, bangla: 'শূন্য', ipa: '[ʃunːo]', romanisation: 'shunnô', english: 'Zero' },
  { digit: '১', value: 1, bangla: 'এক', ipa: '[æk]', romanisation: 'æk', english: 'One' },
  { digit: '২', value: 2, bangla: 'দুই', ipa: '[d̪ui]', romanisation: 'dui', english: 'Two' },
  { digit: '৩', value: 3, bangla: 'তিন', ipa: '[t̪in]', romanisation: 'tin', english: 'Three' },
  { digit: '৪', value: 4, bangla: 'চার', ipa: '[tʃaɾ]', romanisation: 'char', english: 'Four' },
  { digit: '৫', value: 5, bangla: 'পাঁচ', ipa: '[pãtʃ]', romanisation: 'pãch', english: 'Five' },
  { digit: '৬', value: 6, bangla: 'ছয়', ipa: '[tʃʰɔj]', romanisation: 'chhôy', english: 'Six' },
  { digit: '৭', value: 7, bangla: 'সাত', ipa: '[ʃat̪]', romanisation: 'shat', english: 'Seven' },
  { digit: '৮', value: 8, bangla: 'আট', ipa: '[aʈ]', romanisation: 'aṭ', english: 'Eight' },
  { digit: '৯', value: 9, bangla: 'নয়', ipa: '[nɔj]', romanisation: 'nôy', english: 'Nine' },
]
const conversationChapters = [
  {
    id: 'introduction', number: 1, banglaTitle: 'আমার পরিচয়', englishTitle: 'My introduction', sourcePages: '1–2', symbol: 'আমি', tone: 'mint',
    description: 'Introduce yourself by sharing your name, age, class, and school name.',
    lessons: [
      {
        id: 'my-name', scene: 'My name', symbol: '01',
        lines: [
          { speaker: 'প্রশ্ন', bangla: 'তোমার নাম কী?', ipa: '[ˈt̪omaɾ nam ki]', romanisation: 'tomar nam ki?', english: 'What is your name?' },
          { speaker: 'উত্তর', bangla: 'আমার নাম তিথি।', ipa: '[ˈamaɾ nam ˈt̪it̪ʰi]', romanisation: 'amar nam Tithi.', english: 'My name is Tithi.' },
        ],
        tip: 'Use আমার নাম … to say your name.',
      },
      {
        id: 'my-age', scene: 'My age', symbol: '02',
        lines: [
          { speaker: 'প্রশ্ন', bangla: 'তোমার বয়স কত?', ipa: '[ˈt̪omaɾ ˈbɔjoʃ ˈkɔt̪o]', romanisation: 'tomar boyosh koto?', english: 'How old are you?' },
          { speaker: 'উত্তর', bangla: 'আমার বয়স সাত বছর।', ipa: '[ˈamaɾ ˈbɔjoʃ ʃat̪ ˈbɔtʃʰɔɾ]', romanisation: 'amar boyosh shat bochhor.', english: 'I am seven years old.' },
        ],
        tip: 'Use আমার বয়স … বছর to say your age.',
      },
      {
        id: 'my-class', scene: 'My class', symbol: '03',
        lines: [
          { speaker: 'প্রশ্ন', bangla: 'তুমি কোন শ্রেণিতে পড়?', ipa: '[ˈt̪umi kon ˈsrenit̪e ˈpɔɽo]', romanisation: 'tumi kon shrenite poro?', english: 'Which class are you in?' },
          { speaker: 'উত্তর', bangla: 'আমি দ্বিতীয় শ্রেণিতে পড়ি।', ipa: '[ˈami d̪it̪ijo ˈsrenit̪e ˈpɔɽi]', romanisation: 'ami ditiyo shrenite pori.', english: 'I am in Class Two.' },
        ],
        tip: 'Use আমি … শ্রেণিতে পড়ি to say your class.',
      },
      {
        id: 'my-school', scene: 'My school', symbol: '04',
        lines: [
          { speaker: 'প্রশ্ন', bangla: 'তোমার বিদ্যালয়ের নাম কী?', ipa: '[ˈt̪omaɾ bid̪d̪alɔjeɾ nam ki]', romanisation: 'tomar bidyaloyer nam ki?', english: 'What is the name of your school?' },
          { speaker: 'উত্তর', bangla: 'আমার বিদ্যালয়ের নাম ______।', ipa: '[ˈamaɾ bid̪d̪alɔjeɾ nam ...]', romanisation: 'amar bidyaloyer nam ______.', english: 'My school’s name is ______.' },
        ],
        tip: 'Complete the sentence with the name of your school.',
      },
    ],
  },
  {
    id: 'school-feelings', number: 2, banglaTitle: 'স্কুলে কেমন লাগছে', englishTitle: 'How school feels', sourcePages: '3–5', symbol: 'স্কুল', tone: 'sky',
    description: 'Talk about feelings, favourite activities, school competitions, and returning to class.',
    lessons: [
      {
        id: 'feelings', scene: 'Talking about school', symbol: '01',
        lines: [
          { speaker: 'বন্ধু', bangla: 'স্কুলে এসে তোমার কেমন লাগছে?', ipa: '[ˈskule ˈeʃe ˈt̪omaɾ ˈkɛmon ˈlaɡtʃʰe]', romanisation: 'skule eshe tomar kemon lagchhe?', english: 'How do you feel after coming to school?' },
          { speaker: 'আমি', bangla: 'অনেক খুশি লাগছে।', ipa: '[ˈɔnɛk ˈkʰuʃi ˈlaɡtʃʰe]', romanisation: 'onek khushi lagchhe.', english: 'I feel very happy.' },
        ],
        tip: 'Change খুশি (happy) to another feeling word when you answer.',
      },
      {
        id: 'hobbies', scene: 'Sharing favourite activities', symbol: '02',
        lines: [
          { speaker: 'মিতু', bangla: 'আমি মিতু। আমি গান গাইতে পছন্দ করি।', ipa: '[ˈami ˈmit̪u | ˈami ˈɡan ˈɡait̪e ˈpɔtʃʰɔnd̪o ˈkoɾi]', romanisation: 'ami Mitu. ami gan gaite pochhondo kori.', english: 'I am Mitu. I like to sing.' },
          { speaker: 'রাজু', bangla: 'আমি রাজু। আমার ছবি আঁকতে ভালো লাগে।', ipa: '[ˈami ˈɾaɟu | ˈamaɾ ˈtʃʰobi ˈãkt̪e ˈbʱalo ˈlaɡe]', romanisation: 'ami Raju. amar chhobi ankte bhalo lage.', english: 'I am Raju. I like drawing pictures.' },
          { speaker: 'তিথি', bangla: 'আমি তিথি। আমি খেলতে পছন্দ করি।', ipa: '[ˈami ˈt̪it̪ʰi | ˈami ˈkʰelt̪e ˈpɔtʃʰɔnd̪o ˈkoɾi]', romanisation: 'ami Tithi. ami khelte pochhondo kori.', english: 'I am Tithi. I like to play.' },
          { speaker: 'বিমিত', bangla: 'আমি বিমিত। আমি পড়তে ভালোবাসি।', ipa: '[ˈami ˈbimit̪ | ˈami ˈpɔɽt̪e bʱalobaʃi]', romanisation: 'ami Bimit. ami porte bhalobashi.', english: 'I am Bimit. I love to read.' },
        ],
        tip: 'Use পছন্দ করি or ভালো লাগে to say what you enjoy doing.',
      },
      {
        id: 'competitions', scene: 'School competitions', symbol: '03',
        lines: [
          { speaker: 'মিতু', bangla: 'জানো, বিদ্যালয়ে খেলাধুলার প্রতিযোগিতা হবে?', ipa: '[ˈɟano bid̪d̪alɔje kʰelad̪ʱulaɾ pɾot̪iɟoɡit̪a hɔbe]', romanisation: 'jano, bidyaloye kheladhular protijogita hobe?', english: 'Did you know there will be a sports competition at school?' },
          { speaker: 'রাজু', bangla: 'গান আর ছবি আঁকার প্রতিযোগিতাও হবে।', ipa: '[ɡan aɾ tʃʰobi ãkaɾ pɾot̪iɟoɡit̪ao hɔbe]', romanisation: 'gan ar chhobi ankar protijogitao hobe.', english: 'There will also be singing and drawing competitions.' },
        ],
        tip: 'প্রতিযোগিতা means “competition”.',
      },
      {
        id: 'choosing-activities', scene: 'Choosing activities', symbol: '04',
        lines: [
          { speaker: 'তিথি', bangla: 'আমি দৌড়ে লাফ দেব। তুমি?', ipa: '[ˈami d̪ouɽe lapʰ d̪ebo | ˈt̪umi]', romanisation: 'ami doure laf debo. tumi?', english: 'I will run and jump. And you?' },
          { speaker: 'বিমিত', bangla: 'আমি ছবি আঁকব। পাহাড়ের ছবি।', ipa: '[ˈami tʃʰobi ãkbo | pahaɽeɾ tʃʰobi]', romanisation: 'ami chhobi ankbo. paharer chhobi.', english: 'I will draw a picture—a picture of a mountain.' },
          { speaker: 'মিতু', bangla: 'আমি একটা দেশের গান গাইব।', ipa: '[ˈami ɛkʈa d̪eʃeɾ ɡan ɡaibo]', romanisation: 'ami ekta desher gan gaibo.', english: 'I will sing a patriotic song.' },
          { speaker: 'রাজু', bangla: 'আমি ছড়া বলব।', ipa: '[ˈami tʃʰɔɽa bolbo]', romanisation: 'ami chhora bolbo.', english: 'I will recite a rhyme.' },
        ],
        tip: 'The classmates choose different competition activities.',
      },
      {
        id: 'back-to-class', scene: 'Returning to class', symbol: '05',
        lines: [
          { speaker: 'তিথি', bangla: 'দারুণ, খুব ভালো হবে।', ipa: '[d̪aɾun kʰub bʱalo hɔbe]', romanisation: 'darun, khub bhalo hobe.', english: 'Great, it will be very good.' },
          { speaker: 'মিতু', bangla: 'ওই যে ঘণ্টা পড়ল। চলো, ক্লাসে যাই।', ipa: '[oi dʒe ɡʱɔnʈa pɔɽlo | tʃɔlo klase dʒai]', romanisation: 'oi je ghonta porlo. cholo, klase jai.', english: 'The bell has rung. Come on, let’s go to class.' },
        ],
        tip: 'চলো means “let’s go”.',
      },
    ],
  },
  {
    id: 'home-work', number: 3, banglaTitle: 'আমার বাড়ি আমার কাজ', englishTitle: 'My home, my work', sourcePages: '6', symbol: 'বাড়ি', tone: 'sun',
    description: 'Follow a family conversation about housework, shopping, and helping one another.',
    lessons: [
      {
        id: 'plans', scene: 'Planning the work', symbol: '01',
        lines: [
          { speaker: 'মা', bangla: 'আজ অনেক কাজ করতে হবে।', ipa: '[aɟ ˈɔnɛk kaɟ ˈkoɾt̪e ˈhɔbe]', romanisation: 'aj onek kaj korte hobe.', english: 'There is a lot of work to do today.' },
          { speaker: 'তুলি', bangla: 'কী কাজ, মা?', ipa: '[ki kaɟ | ma]', romanisation: 'ki kaj, ma?', english: 'What work, Mother?' },
          { speaker: 'মা', bangla: 'ঘর-বাড়ি পরিষ্কার করতে হবে। কাপড় গোছাতে হবে।', ipa: '[ɡʱɔɾ ˈbaɽi pɔɾiʃˈkaɾ ˈkoɾt̪e ˈhɔbe | ˈkapɔɽ ˈɡotʃʰat̪e ˈhɔbe]', romanisation: 'ghor-bari porishkar korte hobe. kapor gochhate hobe.', english: 'The house must be cleaned. The clothes must be arranged.' },
        ],
        tip: 'Mother explains which household jobs need to be done.',
      },
      {
        id: 'market-plan', scene: 'Going to the market', symbol: '02',
        lines: [
          { speaker: 'তপু', bangla: 'আমিও কাজ করব।', ipa: '[ˈamio kaɟ ˈkoɾbo]', romanisation: 'amio kaj korbo.', english: 'I will help with the work too.' },
          { speaker: 'বাবা', bangla: 'আজ তো বাজারেও যেতে হবে।', ipa: '[aɟ t̪o badʒaɾeo dʒet̪e hɔbe]', romanisation: 'aj to bajareo jete hobe.', english: 'We also have to go to the market today.' },
          { speaker: 'তপু', bangla: 'আমি তাহলে বাবার সঙ্গে বাজারে যাই।', ipa: '[ˈami t̪ahole babaɾ ʃɔŋɡe badʒaɾe dʒai]', romanisation: 'ami tahole babar shonge bajare jai.', english: 'Then I will go to the market with Father.' },
        ],
        tip: 'Topu offers to go to the market with Father.',
      },
      {
        id: 'helping-mother', scene: 'Helping mother', symbol: '03',
        lines: [
          { speaker: 'তুলি', bangla: 'আমি তবে মার সঙ্গে কাজ করি।', ipa: '[ˈami t̪obe maɾ ʃɔŋɡe kaɟ koɾi]', romanisation: 'ami tobe mar shonge kaj kori.', english: 'Then I will work with Mother.' },
          { speaker: 'বাবা', bangla: 'কী করবে?', ipa: '[ki koɾbe]', romanisation: 'ki korbe?', english: 'What will you do?' },
          { speaker: 'তুলি', bangla: 'ঘর পরিষ্কার করব। কাপড় গোছাব।', ipa: '[ɡʱɔɾ pɔɾiʃkaɾ koɾbo | kapɔɽ ɡotʃʰabo]', romanisation: 'ghor porishkar korbo. kapor gochhabo.', english: 'I will clean the house and arrange the clothes.' },
        ],
        tip: 'Tuli explains how she will help Mother.',
      },
      {
        id: 'together', scene: 'Working together', symbol: '04',
        lines: [
          { speaker: 'মা', bangla: 'ঠিক আছে। সবাই মিলে কাজ করব।', ipa: '[ˈʈʰik ˈatʃʰe | ˈʃɔbai ˈmile kaɟ ˈkoɾbo]', romanisation: 'thik ache. shobai mile kaj korbo.', english: 'All right. We will all work together.' },
          { speaker: 'বাবা', bangla: 'মিলেমিশে করলে কাজ সহজ হয়।', ipa: '[mileˈmiʃe ˈkoɾle kaɟ ˈʃɔhoɟ hɔe̯]', romanisation: 'milemishe korle kaj shohoj hoy.', english: 'Work becomes easier when everyone works together.' },
        ],
        tip: 'The lesson ends with the idea that shared work is easier.',
      },
    ],
  },
  {
    id: 'dalim-kumar', number: 4, format: 'article', banglaTitle: 'ডালিমকুমার ও কঙ্কাবতী', englishTitle: 'Dalim Kumar and Kankabati', sourcePages: '7–11', symbol: 'গল্প', tone: 'peach',
    description: 'Read the story of a prince, a captive princess, and a brave rescue from the demon’s land.',
    lessons: [
      {
        id: 'the-wandering-prince', scene: 'The wandering prince', symbol: '01', banglaHeading: 'রাজপুত্রের যাত্রা',
        paragraphs: [
          { bangla: 'এক ছিল রাজপুত্র। তার নাম ডালিমকুমার।', english: 'Once there was a prince. His name was Dalim Kumar.' },
          { bangla: 'তার ছিল এক পক্ষীরাজ ঘোড়া। ঘোড়ায় চড়ে সে দেশে-বিদেশে ঘুরে বেড়াত।', english: 'He had a winged horse. He rode it and travelled through many lands.' },
          { bangla: 'একবার ঘুরতে ঘুরতে অচিনপুরে চলে এলো। সে অনেক ক্লান্ত বোধ করল। সে গাছের ছায়ায় ঘুমিয়ে পড়ল।', english: 'One day he arrived in an unknown land. Feeling very tired, he fell asleep in the shade of a tree.' },
          { bangla: 'ওই গাছে থাকত ব্যাঙ্গমা আর ব্যাঙ্গমি। তারা কথা বলছিল।', english: 'Byangama and Byangami lived in that tree. They were talking.' },
        ],
      },
      {
        id: 'the-captive-princess', scene: 'The captive princess', symbol: '02', banglaHeading: 'বন্দি রাজকন্যা',
        paragraphs: [
          { bangla: 'ডালিমকুমারের ঘুম ভেঙে গেল। ব্যাঙ্গমা বলল, “রাজকন্যা কঙ্কাবতীর কী হয়েছে জানো?”', english: 'Dalim Kumar woke up. Byangama asked, “Do you know what has happened to Princess Kankabati?”' },
          { bangla: 'ব্যাঙ্গমি বলল, “সে এখন রাক্ষসপুরীতে বন্দি।” ব্যাঙ্গমা বলল, “কী সর্বনাশ!”', english: 'Byangami said, “She is being held captive in the demon’s land.” Byangama cried, “What a disaster!”' },
          { bangla: 'রাক্ষসপুরী অনেক দূরে। সাত সাগর তেরো নদীর ওপারে।', english: 'The demon’s land was very far away, beyond seven seas and thirteen rivers.' },
          { bangla: 'ডালিমকুমার সাত সাগর তেরো নদী পার হলো। তারপর রাক্ষসপুরীতে পৌঁছাল।', english: 'Dalim Kumar crossed seven seas and thirteen rivers. Then he reached the demon’s land.' },
        ],
      },
      {
        id: 'the-magic-sticks', scene: 'The magic sticks', symbol: '03', banglaHeading: 'সোনার ও রূপার কাঠি',
        paragraphs: [
          { bangla: 'তখন রাজকন্যা কঙ্কাবতী সোনার পালঙ্কে ঘুমিয়ে আছে। কিছুতেই তার ঘুম ভাঙে না।', english: 'Princess Kankabati was asleep on a golden bed. Nothing could wake her.' },
          { bangla: 'ডালিমকুমার দেখতে পেল কঙ্কাবতীর মাথার কাছে রূপার কাঠি। আর পায়ের কাছে সোনার কাঠি।', english: 'Dalim Kumar saw a silver stick near her head and a golden stick near her feet.' },
          { bangla: 'তখন ডালিমকুমার মাথার কাছে সোনার কাঠি নিয়ে এলো। আর পায়ের কাছে নিয়ে এলো রূপার কাঠি।', english: 'He placed the golden stick near her head and the silver stick near her feet.' },
          { bangla: 'অমনি কঙ্কাবতী জেগে উঠল।', english: 'At once, Kankabati woke up.' },
        ],
      },
      {
        id: 'the-demon-arrives', scene: 'The demon arrives', symbol: '04', banglaHeading: 'রাক্ষসের আগমন',
        paragraphs: [
          { bangla: 'ঠিক তখনই রাক্ষস ঘরে ঢুকল।', english: 'Just then, the demon entered the room.' },
          { bangla: 'সাথে সাথে ডালিমকুমার তরবারি বের করল।', english: 'Dalim Kumar immediately drew his sword.' },
          { bangla: 'কঙ্কাবতী বলল, “রাক্ষসের প্রাণ আছে একটা টিনের কৌটার ভেতরে।”', english: 'Kankabati said, “The demon’s life is hidden inside a tin box.”' },
          { bangla: 'ডালিমকুমার জানে না সেই কৌটা কোথায়।', english: 'Dalim Kumar did not know where the box was.' },
        ],
      },
      {
        id: 'the-rescue', scene: 'The rescue', symbol: '05', banglaHeading: 'সাহসী কঙ্কাবতী',
        paragraphs: [
          { bangla: 'কঙ্কাবতীর ছিল অনেক সাহস। সে তখন পালঙ্কের নিচ থেকে একটা কৌটা বের করল।', english: 'Kankabati was very brave. She took a box from beneath the bed.' },
          { bangla: 'কৌটা খুলতেই বেরিয়ে এলো একটা ভ্রমর। তখন কঙ্কাবতী তরবারি দিয়ে ভ্রমরটাকে কেটে ফেলল।', english: 'When she opened the box, a bumblebee flew out. Kankabati cut it down with the sword.' },
          { bangla: 'তারপর ডালিমকুমার ও কঙ্কাবতী বেরিয়ে এলো রাক্ষসপুরী থেকে।', english: 'Then Dalim Kumar and Kankabati escaped from the demon’s land.' },
        ],
      },
    ],
  },
]
const consonants = [
  { letter: 'ক', ipa: '[kɔ]', romanisation: 'ka', tipTitle: 'Use a clean, unaspirated “k”', tip: 'It is like the “k” in “skate”. Keep the sound short and do not release a strong puff of air.' },
  { letter: 'খ', ipa: '[kʰɔ]', romanisation: 'kha', tipTitle: 'Add a clear puff after “k”', tip: 'Begin with ক, then release a noticeable breath. Hold a hand in front of your mouth to feel the air.' },
  { letter: 'গ', ipa: '[ɡɔ]', romanisation: 'ga', tipTitle: 'Use the hard “g” sound', tip: 'It is close to the “g” in “go”. Let your voice vibrate and keep the release gentle.' },
  { letter: 'ঘ', ipa: '[ɡʱɔ]', romanisation: 'gha', tipTitle: 'Make a breathy “g” sound', tip: 'Begin with গ and let a soft breath follow it. Keep the sound voiced throughout.' },
  { letter: 'ঙ', ipa: '[ŋɔ]', romanisation: 'ṅa', tipTitle: 'Use the “ng” sound', tip: 'It is like the final sound in “sing”. The back of your tongue stays raised while air passes through your nose.' },
  { letter: 'চ', ipa: '[cɔ]', romanisation: 'ca', tipTitle: 'Use a voiceless palatal stop', tip: 'Raise the middle of the tongue toward the hard palate and release [c] without voicing or extra breath.' },
  { letter: 'ছ', ipa: '[cʰɔ]', romanisation: 'cha', tipTitle: 'Add aspiration to the palatal stop', tip: 'Begin like চ, then release the formal aspirated sound [cʰ] with a clear puff of air.' },
  { letter: 'জ', ipa: '[ɟɔ]', romanisation: 'ja', tipTitle: 'Use a voiced palatal stop', tip: 'Raise the middle of the tongue toward the hard palate and keep the vocal folds vibrating for [ɟ].' },
  { letter: 'ঝ', ipa: '[ɟʱɔ]', romanisation: 'jha', tipTitle: 'Use a breathy voiced palatal stop', tip: 'Begin like জ and maintain voicing while adding the breathy release marked by [ʱ].' },
  { letter: 'ঞ', ipa: '[ŋɔ]', romanisation: 'ña', tipTitle: 'Use the formal nasal value', tip: 'In the official Bangla IPA alignment, ঞ shares the velar nasal value [ŋ] with ঙ and ং.' },
  { letter: 'ট', ipa: '[ʈɔ]', romanisation: 'ṭa', tipTitle: 'Curl the tongue for a firm “t”', tip: 'Touch the curled tongue tip farther back on the roof of your mouth, then release it without a strong puff.' },
  { letter: 'ঠ', ipa: '[ʈʰɔ]', romanisation: 'ṭha', tipTitle: 'Add breath to the curled “t”', tip: 'Use the same tongue position as ট, then release a clearly audible puff of air.' },
  { letter: 'ড', ipa: '[ɖɔ]', romanisation: 'ḍa', tipTitle: 'Use a curled, voiced “d”', tip: 'Curl the tongue tip back as for ট, but let your voice vibrate during the release.' },
  { letter: 'ঢ', ipa: '[ɖʱɔ]', romanisation: 'ḍha', tipTitle: 'Make a breathy curled “d”', tip: 'Begin like ড and add a soft voiced breath immediately after the release.' },
  { letter: 'ণ', ipa: '[nɔ]', romanisation: 'ṇa', tipTitle: 'Use the modern nasal value', tip: 'In standard modern Bangla, ণ is pronounced [n], the same phoneme used for ন, although the spelling remains distinct.' },
  { letter: 'ত', ipa: '[t̪ɔ]', romanisation: 'ta', tipTitle: 'Place the tongue against the teeth', tip: 'Touch the tongue tip lightly behind the upper teeth. This dental “t” is softer than the English “t”.' },
  { letter: 'থ', ipa: '[t̪ʰɔ]', romanisation: 'tha', tipTitle: 'Add breath to the dental “t”', tip: 'Begin with the tongue position for ত, then release a distinct puff of air.' },
  { letter: 'দ', ipa: '[d̪ɔ]', romanisation: 'da', tipTitle: 'Use a dental “d” sound', tip: 'Touch the tongue tip behind the upper teeth and let your voice vibrate as you release it.' },
  { letter: 'ধ', ipa: '[d̪ʱɔ]', romanisation: 'dha', tipTitle: 'Make a breathy dental “d”', tip: 'Begin like দ, then let a soft voiced breath follow without separating the sounds.' },
  { letter: 'ন', ipa: '[nɔ]', romanisation: 'na', tipTitle: 'Use a clear “n” sound', tip: 'It is close to the “n” in “name”. Keep the tongue near the upper teeth and let air pass through the nose.' },
  { letter: 'প', ipa: '[pɔ]', romanisation: 'pa', tipTitle: 'Use a light, unaspirated “p”', tip: 'Close both lips and release them gently. Avoid the strong puff often heard in English “pin”.' },
  { letter: 'ফ', ipa: '[pʰɔ]', romanisation: 'pha', tipTitle: 'Release a puff after “p”', tip: 'Begin like প and follow it with a clear burst of air. Keep the lips doing the work.' },
  { letter: 'ব', ipa: '[bɔ]', romanisation: 'ba', tipTitle: 'Use a voiced “b” sound', tip: 'It is close to the “b” in “book”. Close the lips, turn on your voice, and release gently.' },
  { letter: 'ভ', ipa: '[bʱɔ]', romanisation: 'bha', tipTitle: 'Make a breathy “b” sound', tip: 'Begin like ব and let a soft voiced breath follow the lip release.' },
  { letter: 'ম', ipa: '[mɔ]', romanisation: 'ma', tipTitle: 'Use a smooth “m” sound', tip: 'Close both lips and let the sound resonate through your nose, as in English “mother”.' },
  { letter: 'য', ipa: '[ɟɔ]', romanisation: 'ya', tipTitle: 'Use the voiced palatal value', tip: 'In the official Bangla IPA alignment, য shares the voiced palatal value [ɟ] with জ.' },
  { letter: 'র', ipa: '[rɔ]', romanisation: 'ra', tipTitle: 'Tap the tongue lightly', tip: 'Make a quick light tap behind the upper teeth. Avoid the long English “r” sound.' },
  { letter: 'ল', ipa: '[lɔ]', romanisation: 'la', tipTitle: 'Use a clear “l” sound', tip: 'Touch the tongue tip just behind the upper teeth, similar to the “l” in “light”.' },
  { letter: 'শ', ipa: '[ʃɔ]', romanisation: 'śa', tipTitle: 'Use the “sh” sound', tip: 'It is close to the “sh” in “ship”. Round the lips slightly and let the air flow smoothly.' },
  { letter: 'ষ', ipa: '[ʃɔ]', romanisation: 'ṣa', tipTitle: 'Use the lesson’s “sh” sound', tip: 'In modern Bangla it is usually pronounced like শ. The spelling shows which letter is used.' },
  { letter: 'স', ipa: '[sɔ]', romanisation: 'sa', tipTitle: 'Use a light “s” sound', tip: 'It is close to the “s” in “see”, though its value may shift toward “sh” in some words.' },
  { letter: 'হ', ipa: '[hɔ]', romanisation: 'ha', tipTitle: 'Let the breath flow freely', tip: 'It is close to the “h” in “home”. Keep the throat open and use a gentle stream of air.' },
  { letter: 'ড়', ipa: '[ɽɔ]', romanisation: 'ṛa', tipTitle: 'Use a quick curled tongue flap', tip: 'Curl the tongue tip back and flick it forward once while keeping the sound voiced.' },
  { letter: 'ঢ়', ipa: '[ɽʱɔ]', romanisation: 'ṛha', tipTitle: 'Add breath to the curled flap', tip: 'Begin like ড়, then add a soft breath immediately after the quick tongue movement.' },
  { letter: 'য়', ipa: '[jɔ]', romanisation: 'ya', tipTitle: 'Use a short “y” glide', tip: 'It is close to the “y” in “yes”. Move smoothly into the vowel that follows.' },
  { letter: 'ৎ', ipa: '[t̪]', romanisation: 't', tipTitle: 'Use the shortened “t” sign', tip: 'This special consonant form gives a brief dental “t” sound and normally appears within a word.' },
  { letter: 'ং', displayLetter: 'অং', category: 'special', ipa: '[ɔŋ]', romanisation: 'aṃ', tipTitle: 'Add a nasal “ng” sound', tip: 'The sign ং is shown with অ so that it renders in context. In অং, it contributes the velar nasal [ŋ].' },
  { letter: 'ঃ', displayLetter: 'অঃ', category: 'special', ipa: '[ɔh]', romanisation: 'aḥ', tipTitle: 'Release a light final breath', tip: 'The sign ঃ is shown with অ because it normally follows another sound. In অঃ, it contributes a light [h]-like release.' },
  { letter: 'ঁ', displayLetter: 'অঁ', category: 'special', ipa: '[ɔ̃]', romanisation: 'ã', tipTitle: 'Nasalise the vowel', tip: 'The sign ঁ is shown above অ because it cannot stand alone. In অঁ, the tilde in [ɔ̃] marks a nasalised vowel.' },
]
const currentVowel = computed(() => vowels[currentVowelIndex.value])
const currentVowelNumber = computed(() => currentVowelIndex.value + 1)
const currentWord = computed(() => wordBlendingItems[currentWordIndex.value])
const currentWordNumber = computed(() => currentWordIndex.value + 1)
const currentNumber = computed(() => numberItems[currentNumberIndex.value])
const currentNumberNumber = computed(() => currentNumberIndex.value + 1)
const currentConversationChapter = computed(() => conversationChapters[currentConversationChapterIndex.value])
const currentConversationLessons = computed(() => currentConversationChapter.value.lessons)
const currentConversation = computed(() => currentConversationLessons.value[currentConversationIndex.value])
const currentConversationNumber = computed(() => currentConversationIndex.value + 1)
const currentConsonant = computed(() => consonants[currentConsonantIndex.value])
const currentConsonantNumber = computed(() => currentConsonantIndex.value + 1)
const currentConsonantCanBlend = computed(() => currentConsonant.value.category !== 'special' && currentConsonant.value.letter !== 'ৎ')
const currentConsonantVowel = computed(() => consonantVowels[currentConsonantVowelIndex.value])
const currentConsonantBaseIpa = computed(() => currentConsonant.value.ipa.replace(/^\[/, '').replace(/\]$/, '').replace(/ɔ$/, ''))
const currentConsonantBaseRomanisation = computed(() => currentConsonant.value.romanisation.replace(/a$/, ''))
const currentConsonantCombination = computed(() => currentConsonantCanBlend.value ? `${currentConsonant.value.letter}${currentConsonantVowel.value.sign}` : (currentConsonant.value.displayLetter || currentConsonant.value.letter))
const currentConsonantCombinationIpa = computed(() => currentConsonantCanBlend.value ? `[${currentConsonantBaseIpa.value}${currentConsonantVowel.value.ipa}]` : currentConsonant.value.ipa)
const currentConsonantCombinationRomanisation = computed(() => currentConsonantCanBlend.value ? `${currentConsonantBaseRomanisation.value}${currentConsonantVowel.value.romanisation}` : currentConsonant.value.romanisation)
const currentConsonantSpokenIpa = computed(() => currentConsonantCombinationIpa.value.replace(/^\[/, '').replace(/\]$/, ''))
const answeredQuizCount = computed(() => quizData.value?.questions.filter(question =>
  (quizAnswers.value[question.questionID] || []).length > 0).length || 0)
const quizReady = computed(() => !!quizData.value?.questions.length && answeredQuizCount.value === quizData.value.questions.length)
const titles = { login: 'Welcome back.', register: 'Start something wonderful.', forgot: 'Reset your password.', verify: 'Check your inbox.', reset: 'Set a new password.' }
const subtitles = { login: 'A little learning. A world of possibility.', register: 'Create your account and begin your journey.', forgot: 'Enter your email and we will send you a verification code.', verify: 'Enter the six-digit code to continue.', reset: 'Choose a secure password for your account.' }
const isChildCreate = computed(() => !!signedIn.value && page.value === 'child-create')
const isChildEdit = computed(() => isChildCreate.value && editingChildId.value !== null)
const isStudentHome = computed(() => !!signedIn.value && page.value === 'student-home')
const isProfilesHome = computed(() => !!signedIn.value && page.value === 'login')
const studentBackLabel = computed(() => {
  if (studentLesson.value === 'home') return 'Child profiles'
  if (studentLesson.value === 'blending-home' || studentLesson.value === 'numbers') return 'Spelling & words'
  if (studentLesson.value === 'conversations') return 'Reading & conversations'
  return 'Learning home'
})
const isParentPinSet = computed(() => !!signedIn.value && page.value === 'parent-pin-set')
const isParentPinVerify = computed(() => !!signedIn.value && page.value === 'parent-pin')
const isParentPinForgot = computed(() => !!signedIn.value && page.value === 'parent-pin-forgot')
const isParentPinReset = computed(() => !!signedIn.value && page.value === 'parent-pin-reset')
const isParentPlaceholder = computed(() => !!signedIn.value && page.value === 'parent-dashboard')
const currentTitle = computed(() => {
  if (!signedIn.value) return titles[page.value]
  if (isStudentHome.value) return `${studentHome.value?.child?.nickname || 'Student'}’s learning`
  if (isChildCreate.value) return isChildEdit.value ? 'Edit child profile' : 'Add child profile'
  if (isParentPinSet.value) return 'Set parent PIN'
  if (isParentPinVerify.value) return 'Enter parent area'
  if (isParentPinForgot.value) return 'Reset parent PIN'
  if (isParentPinReset.value) return 'Choose a new parent PIN'
  if (isParentPlaceholder.value) return 'Parent area'
  return 'Child profiles'
})
const currentSubtitle = computed(() => {
  if (!signedIn.value) return subtitles[page.value]
  if (isStudentHome.value) return studentHome.value?.level?.description || 'Choose a lesson and keep learning.'
  if (isChildCreate.value) return isChildEdit.value ? 'Update their profile details.' : 'Create a space that feels like their own.'
  if (isParentPinSet.value) return 'A small PIN keeps parent-only areas safe.'
  if (isParentPinVerify.value) return 'Enter your 4-digit PIN to continue.'
  if (isParentPinForgot.value) return 'Enter the verification code sent to your registered email.'
  if (isParentPinReset.value) return 'Choose a new 4-digit PIN for parent-only areas.'
  if (isParentPlaceholder.value) return 'Parent access has been verified.'
  return 'Create a profile for each child who uses this account.'
})
const cooldown = computed(() => Math.max(0, Math.ceil(((challenge.value?.resend_at || 0) * 1000 - now.value) / 1000)))
const deleteCooldown = computed(() => Math.max(0, Math.ceil(((deleteChallenge.value?.resend_at || 0) * 1000 - now.value) / 1000)))
const timer = setInterval(() => now.value = Date.now(), 1000)
onUnmounted(() => {
  clearInterval(timer)
  clearTimeout(lessonCompletionTimer)
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
})

function isCustomAvatar(avatar) {
  return typeof avatar === 'string' && avatar.startsWith('custom:')
}
function avatarSource(avatar) {
  if (isCustomAvatar(avatar)) return `/api/children/avatars/${avatar.slice('custom:'.length)}`
  return avatarSources[avatar] || sproutAvatar
}

function go(next) {
  page.value = next; error.value = ''; notice.value = ''; fieldErrors.value = {}; password.value = ''; confirm.value = ''
  if (next === 'login') { challenge.value = null; code.value = '' }
  nextTick(() => heading.value?.focus())
}
function clearFieldError(field) {
  if (!fieldErrors.value[field]) return
  fieldErrors.value = { ...fieldErrors.value, [field]: '' }
}
function resetChildForm() {
  editingChildId.value = null
  childNickname.value = ''
  childAgeBand.value = 'junior'
  selectedAvatar.value = 'sprout'
  customAvatarName.value = ''
  customAvatarFile.value = null
  existingCustomAvatar.value = ''
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
  customAvatarUrl.value = ''
}
function openChildCreate() {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  resetChildForm()
  go('child-create')
}
function openChildEdit(child) {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  resetChildForm()
  editingChildId.value = child.childID
  childNickname.value = child.nickname
  childAgeBand.value = child.ageBand
  if (isCustomAvatar(child.avatar)) {
    selectedAvatar.value = 'custom'
    existingCustomAvatar.value = child.avatar
    customAvatarUrl.value = avatarSource(child.avatar)
    customAvatarName.value = 'Current custom avatar'
  } else {
    selectedAvatar.value = child.avatar
  }
  go('child-create')
}
function cancelChildCreate() {
  resetChildForm()
  go('login')
}
function openStudentHome(child) {
  cancelDeleteConfirm()
  resetQuiz()
  quizCatalog.value = []
  learningPreview.value = ''
  studentLesson.value = 'home'
  run(async () => {
    const home = await accountApi(`/children/${child.childID}/home`)
    const quizGroups = await Promise.all((home.lessons || []).map(async lesson => {
      const quizzes = await accountApi(`/quizzes?lessonID=${lesson.lessonID}`)
      return quizzes.map(quiz => ({ lesson, quiz }))
    }))
    studentHome.value = home
    quizCatalog.value = quizGroups.flat()
    go('student-home')
  })
}
function closeStudentHome() {
  if (studentLesson.value !== 'home') {
    if (studentLesson.value === 'quiz') {
      studentLesson.value = 'home'
      resetQuiz()
    } else if (studentLesson.value === 'blending-home' || studentLesson.value === 'numbers') {
      studentLesson.value = 'spelling-home'
    } else if (studentLesson.value === 'conversations') {
      studentLesson.value = 'conversation-home'
    } else {
      studentLesson.value = 'home'
    }
    learningPreview.value = ''
    vowelFeedback.value = ''
    consonantFeedback.value = ''
    wordFeedback.value = ''
    flippedConversationLines.value = []
    nextTick(() => heading.value?.focus())
    return
  }
  studentHome.value = null
  quizCatalog.value = []
  resetQuiz()
  learningPreview.value = ''
  go('login')
}
function previewLearningArea(area) {
  if (area.id === 'vowels') {
    studentLesson.value = 'vowels'
    currentVowelIndex.value = 0
    learningPreview.value = ''
    vowelFeedback.value = ''
    nextTick(() => heading.value?.focus())
    return
  }
  if (area.id === 'consonants') {
    studentLesson.value = 'consonants'
    currentConsonantIndex.value = 0
    currentConsonantVowelIndex.value = 0
    learningPreview.value = ''
    consonantFeedback.value = ''
    nextTick(() => heading.value?.focus())
    return
  }
  if (area.id === 'spelling') {
    studentLesson.value = 'spelling-home'
    currentWordIndex.value = 0
    currentNumberIndex.value = 0
    wordFeedback.value = ''
    learningPreview.value = ''
    nextTick(() => heading.value?.focus())
    return
  }
  if (area.id === 'conversation') {
    studentLesson.value = 'conversation-home'
    currentConversationChapterIndex.value = 0
    currentConversationIndex.value = 0
    flippedConversationLines.value = []
    learningPreview.value = ''
    nextTick(() => heading.value?.focus())
    return
  }
  learningPreview.value = `${area.title} activities will be connected in the next learning step.`
}
function resetQuiz() {
  quizData.value = null
  quizLesson.value = null
  quizAnswers.value = {}
  quizResult.value = null
  quizHistory.value = []
}
function openQuiz(lesson, quiz) {
  run(async () => {
    const childID = studentHome.value.child.childID
    const [loadedQuiz, history] = await Promise.all([
      accountApi(`/quizzes/${quiz.quizID}`),
      accountApi(`/children/${childID}/quiz-results?quizID=${quiz.quizID}`),
    ])
    if (loadedQuiz.lessonID !== lesson.lessonID) {
      throw new Error('This quiz is no longer linked to the selected lesson.')
    }
    quizLesson.value = lesson
    quizData.value = loadedQuiz
    quizHistory.value = history
    quizAnswers.value = Object.fromEntries(loadedQuiz.questions.map(question => [question.questionID, []]))
    quizResult.value = null
    studentLesson.value = 'quiz'
    nextTick(() => heading.value?.focus())
  })
}
function isQuizOptionSelected(questionID, optionID) {
  return (quizAnswers.value[questionID] || []).includes(optionID)
}
function toggleQuizOption(question, optionID) {
  const selected = quizAnswers.value[question.questionID] || []
  quizAnswers.value = {
    ...quizAnswers.value,
    [question.questionID]: question.questionKind === 'multiple'
      ? (selected.includes(optionID) ? selected.filter(id => id !== optionID) : [...selected, optionID])
      : [optionID],
  }
}
function submitQuiz() {
  if (!quizReady.value) {
    error.value = 'Answer every question before submitting.'
    return
  }
  run(async () => {
    const childID = studentHome.value.child.childID
    const quizID = quizData.value.quizID
    quizResult.value = await accountApi(`/children/${childID}/quizzes/${quizID}/attempts`, {
      method: 'POST',
      body: {
        answers: quizData.value.questions.map(question => ({
          questionID: question.questionID,
          selectedOptionIDs: quizAnswers.value[question.questionID],
        })),
      },
    })
    quizHistory.value = await accountApi(`/children/${childID}/quiz-results?quizID=${quizID}`)
    nextTick(() => heading.value?.focus())
  })
}
function retryQuiz() {
  quizAnswers.value = Object.fromEntries(quizData.value.questions.map(question => [question.questionID, []]))
  quizResult.value = null
  error.value = ''
  nextTick(() => heading.value?.focus())
}
function quizFeedback(questionID) {
  return quizResult.value?.feedback.find(answer => answer.questionID === questionID)
}
function quizOptionText(question, optionIDs) {
  const ids = new Set(optionIDs || [])
  return question.options.filter(option => ids.has(option.optionID)).map(option => option.optionText).join(', ')
}
function openConversationChapter(index) {
  currentConversationChapterIndex.value = index
  currentConversationIndex.value = 0
  flippedConversationLines.value = []
  studentLesson.value = 'conversations'
  nextTick(() => heading.value?.focus())
}
function openWordLesson() {
  studentLesson.value = 'blending-home'
  currentWordIndex.value = 0
  wordFeedback.value = ''
  nextTick(() => heading.value?.focus())
}
function openNumberLesson() {
  studentLesson.value = 'numbers'
  currentNumberIndex.value = 0
  nextTick(() => heading.value?.focus())
}
function previewWordSound() {
  wordFeedback.value = `Pronunciation audio for ${currentWord.value.word} will be added here later.`
}
function showPreviousWord() {
  if (currentWordIndex.value === 0) return
  currentWordIndex.value -= 1
  wordFeedback.value = ''
}
function showNextWord() {
  if (currentWordIndex.value === wordBlendingItems.length - 1) return
  currentWordIndex.value += 1
  wordFeedback.value = ''
}
function goToWord(index) {
  currentWordIndex.value = index
  wordFeedback.value = ''
}
function finishWordLesson() {
  studentLesson.value = 'spelling-home'
  learningPreview.value = ''
  wordFeedback.value = ''
  completedLesson.value = 'Bangla words'
  clearTimeout(lessonCompletionTimer)
  lessonCompletionTimer = setTimeout(() => {
    completedLesson.value = ''
  }, 2400)
  nextTick(() => heading.value?.focus())
}
function showPreviousNumber() {
  if (currentNumberIndex.value === 0) return
  currentNumberIndex.value -= 1
}
function showNextNumber() {
  if (currentNumberIndex.value === numberItems.length - 1) return
  currentNumberIndex.value += 1
}
function goToNumber(index) {
  currentNumberIndex.value = index
}
function finishNumberLesson() {
  studentLesson.value = 'spelling-home'
  learningPreview.value = ''
  completedLesson.value = 'Bangla numbers'
  clearTimeout(lessonCompletionTimer)
  lessonCompletionTimer = setTimeout(() => {
    completedLesson.value = ''
  }, 2400)
  nextTick(() => heading.value?.focus())
}
function showPreviousConversation() {
  if (currentConversationIndex.value === 0) return
  currentConversationIndex.value -= 1
  flippedConversationLines.value = []
}
function showNextConversation() {
  if (currentConversationIndex.value === currentConversationLessons.value.length - 1) return
  currentConversationIndex.value += 1
  flippedConversationLines.value = []
}
function goToConversation(index) {
  currentConversationIndex.value = index
  flippedConversationLines.value = []
}
function isConversationLineFlipped(index) {
  return flippedConversationLines.value.includes(index)
}
function toggleConversationLine(index) {
  flippedConversationLines.value = isConversationLineFlipped(index)
    ? flippedConversationLines.value.filter((lineIndex) => lineIndex !== index)
    : [...flippedConversationLines.value, index]
}
function finishConversationLesson() {
  studentLesson.value = 'conversation-home'
  flippedConversationLines.value = []
  learningPreview.value = ''
  completedLesson.value = `Chapter ${currentConversationChapter.value.number}: ${currentConversationChapter.value.englishTitle}`
  clearTimeout(lessonCompletionTimer)
  lessonCompletionTimer = setTimeout(() => {
    completedLesson.value = ''
  }, 2400)
  nextTick(() => heading.value?.focus())
}
function selectConsonantVowel(index) {
  currentConsonantVowelIndex.value = index
  consonantFeedback.value = ''
}
// Load the Bengali letter MP3 files already stored under src/assets/audio/.
// Examples: 01_অ.mp3, 12_ক.mp3, 13_খ.mp3
const letterAudioFiles = import.meta.glob('../assets/audio/*.mp3', {
  eager: true,
  query: '?url',
  import: 'default',
})
let activeLetterAudio = null

async function playLetterAudio(letter, feedback) {
  const match = Object.entries(letterAudioFiles).find(([path]) => {
    const filename = path.split('/').pop()
    const filenameLetter = filename.replace(/^[^_]*_/, '').replace(/\.mp3$/i, '')
    return filenameLetter.normalize('NFC') === letter.normalize('NFC')
  })

  if (!match) {
    feedback.value = `No MP3 file found for ${letter}. Check src/assets/audio/.`
    return
  }

  try {
    if (activeLetterAudio) activeLetterAudio.pause()
    activeLetterAudio = new Audio(match[1])
    await activeLetterAudio.play()
    feedback.value = ''
  } catch (error) {
    feedback.value = `Could not play the pronunciation for ${letter}.`
    console.error(error)
  }
}

function previewVowelSound() {
  playLetterAudio(currentVowel.value.letter, vowelFeedback)
}
function showPreviousVowel() {
  if (currentVowelIndex.value === 0) return
  currentVowelIndex.value -= 1
  vowelFeedback.value = ''
}
function showNextVowel() {
  if (currentVowelIndex.value === vowels.length - 1) return
  currentVowelIndex.value += 1
  vowelFeedback.value = ''
}
function goToVowel(index) {
  currentVowelIndex.value = index
  vowelFeedback.value = ''
}
function finishVowelLesson() {
  studentLesson.value = 'home'
  learningPreview.value = ''
  vowelFeedback.value = ''
  completedLesson.value = 'Vowels'
  clearTimeout(lessonCompletionTimer)
  lessonCompletionTimer = setTimeout(() => {
    completedLesson.value = ''
  }, 2400)
  nextTick(() => heading.value?.focus())
}
function previewConsonantSound() {
  if (currentConsonantCanBlend.value && currentConsonantVowelIndex.value !== 0) {
    consonantFeedback.value = 'Only the standalone consonant audio is available; combined vowel sounds need separate MP3 files.'
    return
  }
  playLetterAudio(currentConsonant.value.letter, consonantFeedback)
}
function showPreviousConsonant() {
  if (currentConsonantIndex.value === 0) return
  currentConsonantIndex.value -= 1
  consonantFeedback.value = ''
}
function showNextConsonant() {
  if (currentConsonantIndex.value === consonants.length - 1) return
  currentConsonantIndex.value += 1
  consonantFeedback.value = ''
}
function goToConsonant(index) {
  currentConsonantIndex.value = index
  consonantFeedback.value = ''
}
function finishConsonantLesson() {
  studentLesson.value = 'home'
  learningPreview.value = ''
  consonantFeedback.value = ''
  completedLesson.value = 'Consonants'
  clearTimeout(lessonCompletionTimer)
  lessonCompletionTimer = setTimeout(() => {
    completedLesson.value = ''
  }, 2400)
  nextTick(() => heading.value?.focus())
}
function openDeleteConfirm(childId) {
  deleteConfirmId.value = childId
  deleteChallenge.value = null
  deleteCode.value = ''
  clearFieldError('deleteCode')
}
function cancelDeleteConfirm() {
  deleteConfirmId.value = null
  deleteChallenge.value = null
  deleteCode.value = ''
  clearFieldError('deleteCode')
}
function requestDeleteCode(child) {
  run(async () => {
    deleteChallenge.value = await accountApi(`/children/${child.childID}/delete-code`, { method: 'POST', body: {} })
    deleteCode.value = ''
    now.value = Date.now()
  }, { field: 'deleteCode' })
}
function resendDeleteCode() {
  if (!deleteChallenge.value || deleteCooldown.value) return
  run(async () => {
    deleteChallenge.value = await accountApi('/auth/resend-code', {
      method: 'POST',
      body: { challenge_id: deleteChallenge.value.challenge_id },
    })
    deleteCode.value = ''
    now.value = Date.now()
  }, { field: 'deleteCode' })
}
function confirmDeleteChild(child) {
  if (!/^\d{6}$/.test(deleteCode.value)) {
    fieldErrors.value = { ...fieldErrors.value, deleteCode: 'Enter the 6-digit verification code.' }
    return
  }
  run(async () => {
    await accountApi(`/children/${child.childID}`, {
      method: 'DELETE',
      body: { challenge_id: deleteChallenge.value.challenge_id, code: deleteCode.value },
    })
    cancelDeleteConfirm()
    await loadChildren()
    notice.value = `${child.nickname}'s profile was deleted.`
  }, { field: 'deleteCode' })
}
function openPinEditor() {
  pinEditorOpen.value = true
  parentPin.value = ''
  confirmParentPin.value = ''
  fieldErrors.value = {}
  error.value = ''
  notice.value = ''
  go('parent-pin-set')
}
function cancelPinEditor() {
  pinEditorOpen.value = false
  parentPin.value = ''
  confirmParentPin.value = ''
  clearFieldError('pin')
  clearFieldError('pinConfirm')
  if (signedIn.value && page.value === 'parent-pin-set') go('login')
}
function submitParentPin() {
  const next = {}
  if (!/^\d{4}$/.test(parentPin.value)) next.pin = 'Enter a 4-digit PIN.'
  if (!confirmParentPin.value) next.pinConfirm = 'Enter the PIN again.'
  else if (parentPin.value !== confirmParentPin.value) next.pinConfirm = 'The PINs do not match.'
  fieldErrors.value = next
  if (Object.keys(next).length) return
  run(async () => {
    await accountApi('/auth/pin', { method: 'PUT', body: { pin: parentPin.value } })
    signedIn.value = { ...signedIn.value, hasPin: true }
    cancelPinEditor()
    notice.value = 'Your parent PIN has been set.'
  }, { field: 'pin' })
}
function openParentArea() {
  parentAccessPin.value = ''
  pinEditorOpen.value = false
  go('parent-pin')
}
function closeParentArea() {
  parentAccessPin.value = ''
  go('login')
}
function verifyParentAccess() {
  if (!/^\d{4}$/.test(parentAccessPin.value)) {
    fieldErrors.value = { ...fieldErrors.value, parentAccessPin: 'Enter your 4-digit PIN.' }
    return
  }
  run(async () => {
    await accountApi('/auth/pin/verify', { method: 'POST', body: { pin: parentAccessPin.value } })
    parentAccessPin.value = ''
    go('parent-dashboard')
    notice.value = 'Parent access verified.'
  }, { field: 'parentAccessPin' })
}
function startParentPinReset() {
  run(async () => {
    challenge.value = await accountApi('/auth/pin/forgot', { method: 'POST', body: {} })
    code.value = ''
    now.value = Date.now()
    go('parent-pin-forgot')
  })
}
function verifyParentPinResetCode() {
  if (!/^\d{6}$/.test(code.value)) {
    fieldErrors.value = { ...fieldErrors.value, code: 'Enter the 6-digit verification code.' }
    return
  }
  run(async () => {
    const result = await accountApi('/auth/verify-code', {
      method: 'POST',
      body: { challenge_id: challenge.value.challenge_id, code: code.value },
    })
    if (!result.pin_reset) throw new Error('The PIN reset request is invalid.')
    parentPin.value = ''
    confirmParentPin.value = ''
    go('parent-pin-reset')
    notice.value = 'Code verified. Choose your new parent PIN.'
  }, { field: 'code' })
}
function submitParentPinReset() {
  const next = {}
  if (!/^\d{4}$/.test(parentPin.value)) next.pin = 'Enter a 4-digit PIN.'
  if (!confirmParentPin.value) next.pinConfirm = 'Enter the PIN again.'
  else if (parentPin.value !== confirmParentPin.value) next.pinConfirm = 'The PINs do not match.'
  fieldErrors.value = next
  if (Object.keys(next).length) return
  run(async () => {
    await accountApi('/auth/pin/reset', {
      method: 'POST',
      body: { challenge_id: challenge.value.challenge_id, new_pin: parentPin.value },
    })
    challenge.value = null
    code.value = ''
    parentPin.value = ''
    confirmParentPin.value = ''
    parentAccessPin.value = ''
    go('parent-pin')
    notice.value = 'Your parent PIN has been reset. Enter the new PIN to continue.'
  }, { field: 'pin' })
}
function cancelParentPinReset() {
  challenge.value = null
  code.value = ''
  parentPin.value = ''
  confirmParentPin.value = ''
  go('parent-pin')
}
function selectAvatar(id) {
  selectedAvatar.value = id
  clearFieldError('avatar')
}
function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    fieldErrors.value = { ...fieldErrors.value, avatar: 'Choose a PNG, JPG, or WebP image.' }
    event.target.value = ''
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    fieldErrors.value = { ...fieldErrors.value, avatar: 'Choose an image smaller than 2 MB.' }
    event.target.value = ''
    return
  }
  if (customAvatarUrl.value.startsWith('blob:')) URL.revokeObjectURL(customAvatarUrl.value)
  customAvatarUrl.value = URL.createObjectURL(file)
  customAvatarName.value = file.name
  customAvatarFile.value = file
  selectedAvatar.value = 'custom'
  clearFieldError('avatar')
}
function submitChildProfile() {
  const next = {}
  const nickname = childNickname.value.trim()
  if (!nickname) next.nickname = "Enter the child's nickname."
  else if (nickname.length > 60) next.nickname = 'Nickname must be no more than 60 characters.'
  if (!['junior', 'senior'].includes(childAgeBand.value)) next.ageBand = 'Choose an age group.'
  if (selectedAvatar.value === 'custom' && !customAvatarFile.value && !existingCustomAvatar.value) {
    next.avatar = 'Choose an image to use as the custom avatar.'
  }
  fieldErrors.value = next
  if (Object.keys(next).length) return
  run(async () => {
    const childId = editingChildId.value
    let avatar = selectedAvatar.value
    if (avatar === 'custom') {
      if (customAvatarFile.value) {
        const uploaded = await accountApi('/children/avatar', {
          method: 'POST',
          body: customAvatarFile.value,
        })
        avatar = uploaded.avatar
      } else {
        avatar = existingCustomAvatar.value
      }
    }
    await accountApi(childId === null ? '/children' : `/children/${childId}`, {
      method: childId === null ? 'POST' : 'PUT',
      body: { nickname, ageBand: childAgeBand.value, avatar },
    })
    await loadChildren()
    resetChildForm()
    go('login')
    notice.value = childId === null ? 'Child profile created successfully.' : 'Child profile updated successfully.'
  })
}
async function loadChildren() {
  childrenLoading.value = true
  try {
    children.value = await accountApi('/children')
  } finally {
    childrenLoading.value = false
  }
}
function errorField(exception) {
  if (!exception.status || exception.status >= 500) return null
  if (page.value === 'reset' && exception.fields?.includes('new_password')) return 'password'
  if (exception.fields?.length) return exception.fields[0]
  if (page.value === 'verify') return 'code'
  if (page.value === 'forgot') return 'email'
  if (page.value === 'register' && exception.status === 409) return 'email'
  if (page.value === 'child-create') return null
  return 'password'
}
function validateFields() {
  const next = {}
  if (['login', 'register', 'forgot'].includes(page.value)) {
    const normalizedEmail = email.value.trim()
    if (!normalizedEmail) next.email = 'Enter your email address.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) next.email = 'Enter a valid email address.'
  }
  if (['login', 'register', 'reset'].includes(page.value)) {
    if (!password.value) next.password = page.value === 'login' ? 'Please enter your password.' : page.value === 'reset' ? 'Enter your new password.' : 'Enter your password.'
    else if (['register', 'reset'].includes(page.value) && password.value.length < 8) next.password = 'Password must be at least 8 characters.'
    else if (['register', 'reset'].includes(page.value) && password.value.length > 128) next.password = 'Password must be no more than 128 characters.'
  }
  if (['register', 'reset'].includes(page.value)) {
    if (!confirm.value) next.confirm = page.value === 'reset' ? 'Enter your new password again.' : 'Enter your password again.'
    else if (password.value !== confirm.value) next.confirm = 'Your passwords do not match.'
  }
  if (page.value === 'verify' && !/^\d{6}$/.test(code.value)) {
    next.code = 'Enter the 6-digit verification code.'
  }
  fieldErrors.value = next
  return Object.keys(next).length === 0
}
async function run(action, { field } = {}) {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { await action() }
  catch (e) {
    const target = field || errorField(e)
    if (target) fieldErrors.value = { ...fieldErrors.value, [target]: e.message }
    else error.value = e.message
  }
  finally { busy.value = false }
}
onMounted(async () => {
  try {
    const config = await accountApi('/auth/config')
    developmentCodes.value = config.development_codes
    try {
      signedIn.value = await accountApi('/auth/me')
      email.value = signedIn.value.email
      await loadChildren()
    } catch (e) { if (e.status !== 401) throw e }
  } catch (e) {
    if (![0, 404].includes(e.status)) error.value = e.message
  }
  finally { booting.value = false }
})
function submit() {
  if (!validateFields()) return
  run(async () => {
    if (page.value === 'verify') {
      const result = await accountApi('/auth/verify-code', { method: 'POST', body: { challenge_id: challenge.value.challenge_id, code: code.value } })
      if (flow.value === 'forgot' && result.password_reset) {
        go('reset')
        notice.value = 'Code verified. Set your new password.'
        return
      }
      signedIn.value = result.user; email.value = result.user.email
      await loadChildren()
      go('login')
      if (flow.value === 'register') notice.value = 'Account created successfully. You are signed in.'
      return
    }
    if (page.value === 'reset') {
      await accountApi('/auth/reset-password', { method: 'POST', body: { challenge_id: challenge.value.challenge_id, new_password: password.value } })
      go('login')
      notice.value = 'Your password has been reset. Log in with your new password.'
      return
    }
    if (page.value === 'login') {
      const result = await accountApi('/auth/login', {
        method: 'POST',
        body: { email: email.value.trim(), password: password.value },
      })
      signedIn.value = result.user
      email.value = result.user.email
      password.value = ''
      await loadChildren()
      go('login')
      return
    }
    flow.value = page.value
    const endpoint = page.value === 'forgot' ? 'forgot-password' : page.value
    const body = page.value === 'forgot' ? { email: email.value.trim() } : { email: email.value.trim(), password: password.value }
    challenge.value = await accountApi(`/auth/${endpoint}`, { method: 'POST', body })
    now.value = Date.now(); code.value = ''; go('verify')
  })
}
function resend() {
  if (cooldown.value) return
  run(async () => {
    challenge.value = await accountApi('/auth/resend-code', { method: 'POST', body: { challenge_id: challenge.value.challenge_id } })
    code.value = ''; now.value = Date.now(); notice.value = 'A new code is ready.'
  }, { field: 'code' })
}
function signOut() {
  run(async () => {
    await accountApi('/auth/logout', { method: 'POST', body: {} })
    cancelPinEditor()
    parentAccessPin.value = ''
    resetQuiz()
    quizCatalog.value = []
    signedIn.value = null; children.value = []; studentHome.value = null; email.value = ''; password.value = ''; go('login')
  })
}
</script>

<template>
  <main class="account-page" :class="{ 'student-page': isStudentHome, 'signed-in-page': signedIn && !isStudentHome }">
    <section class="account-content" :class="{ 'profiles-content': signedIn, 'student-content': isStudentHome, 'student-lesson-content': isStudentHome && studentLesson !== 'home' }" aria-labelledby="page-title" :aria-busy="busy || booting">
      <div v-if="signedIn && !booting && !isStudentHome" class="account-session">
        <div class="account-session-pin">
          <button v-if="isChildCreate" class="text-button account-nav-back" type="button" @click="cancelChildCreate">← Back to child profiles</button>
          <button v-else-if="isParentPinSet" class="text-button account-nav-back" type="button" @click="cancelPinEditor">← Back to child profiles</button>
          <button v-else-if="isParentPinForgot || isParentPinReset" class="text-button account-nav-back" type="button" @click="cancelParentPinReset">← Back to parent PIN</button>
          <button v-else-if="isParentPinVerify || isParentPlaceholder" class="text-button account-nav-back" type="button" @click="closeParentArea">← Back to child profiles</button>
          <template v-else-if="signedIn.hasPin">
            <span class="pin-status">PIN protected</span>
            <button class="text-button" type="button" :disabled="busy" @click="openParentArea">Parent area</button>
          </template>
          <button v-else-if="isProfilesHome" class="text-button" type="button" :disabled="busy || pinEditorOpen" @click="openPinEditor">Set parent PIN</button>
        </div>
        <div class="account-session-user">
          <strong>{{ signedIn.email }}</strong>
          <button class="text-button" type="button" :disabled="busy" @click="signOut">Sign out</button>
        </div>
      </div>
      <h1 v-if="!isStudentHome" id="page-title" ref="heading" tabindex="-1">{{ currentTitle }}</h1>
      <p v-if="!isStudentHome" class="subtitle">{{ currentSubtitle }}</p>
      <p v-if="booting" class="notice" role="status">Connecting to your account…</p>
      <p v-if="notice" class="notice" role="status">{{ notice }}</p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <template v-if="!booting">
        <div v-if="!signedIn && ['login', 'register'].includes(page)" class="tabs" aria-label="Account action"><button :disabled="busy" :class="{ active: page === 'login' }" :aria-pressed="page === 'login'" @click="go('login')">Log in</button><button :disabled="busy" :class="{ active: page === 'register' }" :aria-pressed="page === 'register'" @click="go('register')">Create account</button></div>
        <template v-if="signedIn">
          <form v-if="isParentPinSet" class="pin-editor" novalidate @submit.prevent="submitParentPin">
            <fieldset :disabled="busy">
              <div class="pin-editor-icon" aria-hidden="true">
                <svg viewBox="0 0 64 72"><path d="M20 31V21a12 12 0 0 1 24 0v10" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><rect x="12" y="29" width="40" height="34" rx="11" fill="currentColor" opacity=".18"/><path d="M32 42v9" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/><path d="M31 13C22 8 20 2 21 0c8 0 13 4 10 13Zm3-1C35 5 41 1 47 3c0 6-6 11-13 9Z" fill="currentColor" opacity=".7"/></svg>
              </div>
              <p>Choose a PIN that children cannot easily guess.</p>
              <label for="parent-pin">4-digit PIN</label>
              <input id="parent-pin" v-model="parentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pin" :aria-describedby="fieldErrors.pin ? 'pin-error' : undefined" @input="clearFieldError('pin')">
              <p v-if="fieldErrors.pin" id="pin-error" class="field-error" role="alert">{{ fieldErrors.pin }}</p>
              <label for="parent-pin-confirm">Confirm PIN</label>
              <input id="parent-pin-confirm" v-model="confirmParentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pinConfirm" :aria-describedby="fieldErrors.pinConfirm ? 'pin-confirm-error' : undefined" @input="clearFieldError('pinConfirm')">
              <p v-if="fieldErrors.pinConfirm" id="pin-confirm-error" class="field-error" role="alert">{{ fieldErrors.pinConfirm }}</p>
              <div class="pin-editor-actions">
                <button class="secondary" type="button" @click="cancelPinEditor">Cancel</button>
                <button class="primary" type="submit">Set PIN</button>
              </div>
            </fieldset>
          </form>
          <form v-else-if="isParentPinVerify" class="parent-pin-gate" novalidate @submit.prevent="verifyParentAccess">
            <fieldset :disabled="busy">
              <label for="parent-access-pin">Parent PIN</label>
              <input id="parent-access-pin" v-model="parentAccessPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.parentAccessPin" :aria-describedby="fieldErrors.parentAccessPin ? 'parent-access-pin-error' : 'parent-access-pin-hint'" @input="clearFieldError('parentAccessPin')">
              <p v-if="fieldErrors.parentAccessPin" id="parent-access-pin-error" class="field-error" role="alert">{{ fieldErrors.parentAccessPin }}</p>
              <p id="parent-access-pin-hint" class="field-hint">Five incorrect attempts will temporarily lock parent access.</p>
              <button class="primary submit-button" type="submit">{{ busy ? 'Checking…' : 'Continue to parent area' }} <span v-if="!busy" aria-hidden="true">→</span></button>
              <button class="text-button forgot" type="button" :disabled="busy" @click="startParentPinReset">Forgot PIN?</button>
            </fieldset>
          </form>
          <form v-else-if="isParentPinForgot" class="parent-pin-gate" novalidate @submit.prevent="verifyParentPinResetCode">
            <fieldset :disabled="busy">
              <div class="email-summary">Verification for <strong>{{ signedIn.email }}</strong></div>
              <label for="pin-reset-code">6-digit verification code</label>
              <input id="pin-reset-code" v-model="code" class="code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required :aria-invalid="!!fieldErrors.code" :aria-describedby="fieldErrors.code ? 'pin-reset-code-error pin-reset-code-hint' : 'pin-reset-code-hint'" @input="clearFieldError('code')">
              <p v-if="fieldErrors.code" id="pin-reset-code-error" class="field-error" role="alert">{{ fieldErrors.code }}</p>
              <p id="pin-reset-code-hint" class="field-hint">Valid for 10 minutes. Up to 5 attempts.</p>
              <div v-if="challenge?.delivery === 'development'" class="development-code">Local development code: <strong>{{ challenge.development_code }}</strong><br>No email was sent.</div>
              <button class="primary submit-button" type="submit">{{ busy ? 'Checking…' : 'Verify & continue' }} <span v-if="!busy" aria-hidden="true">→</span></button>
              <div class="resend-row"><span>Need another code?</span><button class="text-button" type="button" :disabled="cooldown > 0 || busy" @click="resend">{{ cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code' }}</button></div>
            </fieldset>
          </form>
          <form v-else-if="isParentPinReset" class="pin-editor" novalidate @submit.prevent="submitParentPinReset">
            <fieldset :disabled="busy">
              <p>Choose a PIN that children cannot easily guess.</p>
              <label for="new-parent-pin">New 4-digit PIN</label>
              <input id="new-parent-pin" v-model="parentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pin" :aria-describedby="fieldErrors.pin ? 'new-pin-error' : undefined" @input="clearFieldError('pin')">
              <p v-if="fieldErrors.pin" id="new-pin-error" class="field-error" role="alert">{{ fieldErrors.pin }}</p>
              <label for="new-parent-pin-confirm">Confirm new PIN</label>
              <input id="new-parent-pin-confirm" v-model="confirmParentPin" type="password" inputmode="numeric" autocomplete="off" pattern="[0-9]{4}" maxlength="4" placeholder="••••" :aria-invalid="!!fieldErrors.pinConfirm" :aria-describedby="fieldErrors.pinConfirm ? 'new-pin-confirm-error' : undefined" @input="clearFieldError('pinConfirm')">
              <p v-if="fieldErrors.pinConfirm" id="new-pin-confirm-error" class="field-error" role="alert">{{ fieldErrors.pinConfirm }}</p>
              <div class="pin-editor-actions">
                <button class="secondary" type="button" @click="cancelParentPinReset">Cancel</button>
                <button class="primary" type="submit">Reset PIN</button>
              </div>
            </fieldset>
          </form>
          <section v-else-if="isParentPlaceholder" aria-label="Parent dashboard">
            <ParentDashboard :children="children" />
            <button class="secondary" type="button" @click="closeParentArea">Back to child profiles</button>
          </section>
          <section v-else-if="isStudentHome && studentHome" class="student-home" aria-label="Student learning homepage">
            <nav class="student-nav" aria-label="Student navigation">
              <button class="student-brand" type="button" @click="closeStudentHome">
                <span class="student-brand-mark" aria-hidden="true">অ</span>
                <span><strong>Bangla Learning</strong><small>← {{ studentBackLabel }}</small></span>
              </button>
              <div class="student-nav-account">
                <div class="student-identity">
                  <img class="student-nav-avatar" :class="{ custom: isCustomAvatar(studentHome.child.avatar) }" :src="avatarSource(studentHome.child.avatar)" alt="">
                  <strong>{{ studentHome.child.nickname }}</strong>
                </div>
                <button class="student-signout" type="button" :disabled="busy" @click="signOut">Sign out</button>
              </div>
            </nav>

            <template v-if="studentLesson === 'home'">
              <div class="student-home-content">
                <p v-if="learningPreview" class="learning-preview" role="status">
                  {{ learningPreview }}
                </p>

                <header class="student-welcome">
                  <div class="student-welcome-copy">
                    <span class="student-eyebrow">Welcome back</span>
                    <h1 id="page-title" ref="heading" tabindex="-1">What would you like to learn today?</h1>
                    <p>Choose a learning area and continue your Bangla adventure.</p>
                  </div>
                  <div class="student-level-pill">
                    <span>Current level</span>
                    <strong>{{ studentHome.level?.title || studentHome.child.levelTitle || 'Getting started' }}</strong>
                  </div>
                  <div class="student-welcome-animation-space" aria-hidden="true"></div>
                </header>

                <div class="learning-area-heading">
                  <div>
                    <span class="student-eyebrow">Learning activities</span>
                    <h2>Pick a place to begin</h2>
                  </div>
                  <span>4 learning areas</span>
                </div>

                <div class="learning-area-grid">
                  <button v-for="area in learningAreas" :key="area.id" class="learning-area-card" :class="`learning-area-card--${area.tone}`" type="button" @click="previewLearningArea(area)">
                    <span class="learning-area-symbol" aria-hidden="true">{{ area.symbol }}</span>
                    <span class="learning-area-copy">
                      <small>{{ area.label }}</small>
                      <strong>{{ area.title }}</strong>
                      <span>{{ area.description }}</span>
                    </span>
                    <span class="learning-area-arrow" aria-hidden="true">→</span>
                  </button>
                </div>

                <section v-if="quizCatalog.length" class="quiz-launcher" aria-labelledby="quiz-launcher-title">
                  <div class="learning-area-heading">
                    <div>
                      <span class="student-eyebrow">Knowledge checks</span>
                      <h2 id="quiz-launcher-title">Ready for a quiz?</h2>
                    </div>
                    <span>{{ quizCatalog.length }} available</span>
                  </div>
                  <div class="quiz-launcher-grid">
                    <article v-for="entry in quizCatalog" :key="entry.quiz.quizID" class="quiz-launcher-card">
                      <div>
                        <small>{{ entry.lesson.title }}</small>
                        <strong>{{ entry.quiz.title }}</strong>
                        <span>{{ entry.quiz.questionCount }} questions · Pass mark {{ entry.quiz.passMark }}%</span>
                      </div>
                      <button type="button" :disabled="busy || entry.quiz.questionCount === 0" @click="openQuiz(entry.lesson, entry.quiz)">
                        {{ entry.quiz.questionCount ? 'Start quiz' : 'Coming soon' }} <span v-if="entry.quiz.questionCount" aria-hidden="true">→</span>
                      </button>
                    </article>
                  </div>
                </section>
              </div>
            </template>

            <template v-else-if="studentLesson === 'quiz' && quizData">
              <section class="quiz-page">
                <header class="quiz-header">
                  <div>
                    <span class="student-eyebrow">{{ quizLesson.title }} · Knowledge check</span>
                    <h1 id="page-title" ref="heading" tabindex="-1">{{ quizData.title }}</h1>
                    <p v-if="!quizResult">Complete every question, then submit your answers.</p>
                    <p v-else>Attempt {{ quizResult.attemptNumber }} · {{ quizResult.correctCount }} of {{ quizResult.totalCount }} correct</p>
                  </div>
                  <div class="quiz-progress-pill">
                    <span>{{ quizResult ? 'Score' : 'Answered' }}</span>
                    <strong>{{ quizResult ? `${quizResult.score}%` : `${answeredQuizCount} / ${quizData.questions.length}` }}</strong>
                  </div>
                </header>

                <form v-if="!quizResult" class="quiz-form" @submit.prevent="submitQuiz">
                  <fieldset :disabled="busy">
                    <section v-for="(question, index) in quizData.questions" :key="question.questionID" class="quiz-question">
                      <div class="quiz-question-title">
                        <span>{{ String(index + 1).padStart(2, '0') }}</span>
                        <div>
                          <h2>{{ question.prompt }}</h2>
                          <small v-if="question.questionKind === 'multiple'">Select all correct answers.</small>
                        </div>
                      </div>
                      <div class="quiz-options">
                        <label
                          v-for="option in question.options"
                          :key="option.optionID"
                          :class="{ selected: isQuizOptionSelected(question.questionID, option.optionID) }"
                        >
                          <input
                            :type="question.questionKind === 'multiple' ? 'checkbox' : 'radio'"
                            :name="`question-${question.questionID}`"
                            :checked="isQuizOptionSelected(question.questionID, option.optionID)"
                            @change="toggleQuizOption(question, option.optionID)"
                          >
                          <span lang="bn">{{ option.optionText }}</span>
                        </label>
                      </div>
                    </section>
                    <div class="quiz-submit-row">
                      <span>{{ quizReady ? 'All questions answered.' : `${quizData.questions.length - answeredQuizCount} question${quizData.questions.length - answeredQuizCount === 1 ? '' : 's'} remaining.` }}</span>
                      <button class="primary" type="submit" :disabled="!quizReady || busy">{{ busy ? 'Submitting…' : 'Submit quiz' }}</button>
                    </div>
                  </fieldset>
                </form>

                <section v-else class="quiz-results" aria-live="polite">
                  <div class="quiz-result-banner" :class="{ passed: quizResult.passed }">
                    <span aria-hidden="true">{{ quizResult.passed ? '✓' : '↻' }}</span>
                    <div>
                      <strong>{{ quizResult.passed ? 'Quiz passed!' : 'Keep practising' }}</strong>
                      <p>You scored {{ quizResult.score }}%. The pass mark is {{ quizData.passMark }}%.</p>
                    </div>
                  </div>
                  <div class="quiz-feedback-list">
                    <article v-for="(question, index) in quizData.questions" :key="question.questionID" class="quiz-feedback" :class="{ correct: quizFeedback(question.questionID)?.correct }">
                      <span class="quiz-feedback-number">{{ index + 1 }}</span>
                      <div>
                        <h2>{{ question.prompt }}</h2>
                        <p>Your answer: <strong lang="bn">{{ quizOptionText(question, quizAnswers[question.questionID]) }}</strong></p>
                        <p v-if="!quizFeedback(question.questionID)?.correct">Correct answer: <strong lang="bn">{{ quizOptionText(question, quizFeedback(question.questionID)?.correctOptionIDs) }}</strong></p>
                      </div>
                      <strong>{{ quizFeedback(question.questionID)?.correct ? 'Correct' : 'Review' }}</strong>
                    </article>
                  </div>
                  <div class="quiz-result-actions">
                    <button class="secondary" type="button" @click="closeStudentHome">Back to learning home</button>
                    <button class="primary" type="button" @click="retryQuiz">Try again</button>
                  </div>
                </section>

                <aside v-if="quizHistory.length" class="quiz-history" aria-labelledby="quiz-history-title">
                  <div>
                    <span class="student-eyebrow">Progress</span>
                    <h2 id="quiz-history-title">Previous attempts</h2>
                  </div>
                  <ol>
                    <li v-for="attempt in quizHistory" :key="attempt.resultID">
                      <span>Attempt {{ attempt.attemptNumber }}</span>
                      <strong>{{ attempt.score }}%</strong>
                      <small>{{ attempt.passed ? 'Passed' : 'Keep practising' }}</small>
                    </li>
                  </ol>
                </aside>
              </section>
            </template>

            <template v-else-if="studentLesson === 'spelling-home'">
              <section class="spelling-module-home" aria-labelledby="spelling-module-title">
                <header class="spelling-module-header">
                  <div>
                    <span class="student-eyebrow">Spelling &amp; numbers</span>
                    <h1 id="spelling-module-title" ref="heading" tabindex="-1">Choose a learning module</h1>
                    <p>Build familiar Bangla words or learn the Bangla digits from ০ to ৯.</p>
                  </div>
                  <span class="spelling-module-count">2 modules</span>
                </header>

                <div class="spelling-module-grid">
                  <button class="spelling-module-card spelling-module-card--words" type="button" @click="openWordLesson">
                    <span class="spelling-module-symbol" lang="bn" aria-hidden="true">শব্দ</span>
                    <span class="spelling-module-copy">
                      <small>Build words</small>
                      <strong>Word spelling</strong>
                      <span>Blend letters and vowel signs to read 12 useful illustrated words.</span>
                    </span>
                    <span class="spelling-module-arrow" aria-hidden="true">→</span>
                  </button>

                  <button class="spelling-module-card spelling-module-card--numbers" type="button" @click="openNumberLesson">
                    <span class="spelling-module-symbol" lang="bn" aria-hidden="true">১২৩</span>
                    <span class="spelling-module-copy">
                      <small>Learn digits</small>
                      <strong>Numbers</strong>
                      <span>Match Bangla digits ০–৯ with their names and number values.</span>
                    </span>
                    <span class="spelling-module-arrow" aria-hidden="true">→</span>
                  </button>
                </div>
              </section>
            </template>

            <template v-else-if="studentLesson === 'blending-home'">
              <div class="vowel-lesson-stage word-lesson-stage">
                <aside class="vowel-sidebar-progress consonant-progress-rail" :aria-label="`Word learning progress: ${currentWordNumber} of ${wordBlendingItems.length}`">
                  <span>Word progress</span>
                  <strong>{{ currentWordNumber }} / {{ wordBlendingItems.length }}</strong>
                  <div class="consonant-dot-track" :style="{ '--lesson-steps': wordBlendingItems.length }" role="navigation" aria-label="Jump to a word">
                    <button
                      v-for="(word, index) in wordBlendingItems"
                      :key="word.id"
                      class="consonant-progress-dot"
                      :class="{ completed: index < currentWordIndex, current: index === currentWordIndex }"
                      type="button"
                      :aria-label="`Word ${index + 1}: ${word.word}, ${word.meaning}`"
                      :aria-current="index === currentWordIndex ? 'step' : undefined"
                      :title="`${index + 1}. ${word.word} · ${word.meaning}`"
                      @click="goToWord(index)"
                    ></button>
                  </div>
                </aside>

                <article class="single-vowel-card word-lesson-card" aria-labelledby="word-lesson-title" aria-live="polite">
                  <div class="single-vowel-topline word-lesson-topline">
                    <span class="student-eyebrow">শব্দ · Word {{ String(currentWordNumber).padStart(2, '0') }}</span>
                    <span>{{ currentWord.group }}</span>
                  </div>

                  <div class="word-lesson-main">
                    <div class="word-illustration-shell" role="img" :aria-label="`Illustration of ${currentWord.meaning}`">
                      <img class="word-illustration" :src="currentWord.illustration" alt="">
                    </div>

                    <div class="word-lesson-copy">
                      <span>Bangla word</span>
                      <h1 id="word-lesson-title" ref="heading" tabindex="-1" lang="bn">{{ currentWord.word }}</h1>
                      <div class="word-ipa-row">
                        <strong>{{ currentWord.ipa }}</strong>
                        <button class="vowel-speaker-button" type="button" :aria-label="`Play pronunciation for ${currentWord.word}`" title="Pronunciation audio will be added later" @click="previewWordSound">
                          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10v4h4l5 4V6L8 10H4Zm12.5 2a4.5 4.5 0 0 0-2.1-3.8v7.6a4.5 4.5 0 0 0 2.1-3.8Zm-2.1-8.2v2.1a7 7 0 0 1 0 12.2v2.1a9 9 0 0 0 0-16.4Z"/></svg>
                        </button>
                      </div>
                      <small>Romanised as “{{ currentWord.romanisation }}”</small>
                      <p>{{ currentWord.meaning }}</p>
                    </div>
                  </div>

                  <div class="pronunciation-tip word-blend-tip">
                    <span class="pronunciation-tip-icon" aria-hidden="true">1·2</span>
                    <div>
                      <span class="student-eyebrow">Blend the word</span>
                      <h2 lang="bn">{{ currentWord.parts }}</h2>
                      <p>Say each part slowly, then join the sounds to read <strong lang="bn">{{ currentWord.word }}</strong>.</p>
                    </div>
                  </div>

                  <nav class="vowel-pagination" aria-label="Word pagination">
                    <button type="button" :disabled="currentWordIndex === 0" aria-label="Previous word" title="Previous word" @click="showPreviousWord">
                      <span aria-hidden="true">◀</span>
                    </button>
                    <span>{{ currentWordNumber }}/{{ wordBlendingItems.length }}</span>
                    <button type="button" :aria-label="currentWordIndex === wordBlendingItems.length - 1 ? 'Finish word lesson' : 'Next word'" :title="currentWordIndex === wordBlendingItems.length - 1 ? 'Finish word lesson' : 'Next word'" @click="currentWordIndex === wordBlendingItems.length - 1 ? finishWordLesson() : showNextWord()">
                      <span aria-hidden="true">▶</span>
                    </button>
                  </nav>
                </article>
              </div>
              <p v-if="wordFeedback" class="vowel-feedback" role="status">{{ wordFeedback }}</p>
            </template>

            <template v-else-if="studentLesson === 'numbers'">
              <div class="vowel-lesson-stage number-lesson-stage">
                <aside class="vowel-sidebar-progress consonant-progress-rail" :aria-label="`Number learning progress: ${currentNumberNumber} of ${numberItems.length}`">
                  <span>Number progress</span>
                  <strong>{{ currentNumberNumber }} / {{ numberItems.length }}</strong>
                  <div class="consonant-dot-track" :style="{ '--lesson-steps': numberItems.length }" role="navigation" aria-label="Jump to a number">
                    <button
                      v-for="(number, index) in numberItems"
                      :key="number.value"
                      class="consonant-progress-dot"
                      :class="{ completed: index < currentNumberIndex, current: index === currentNumberIndex }"
                      type="button"
                      :aria-label="`Number ${number.value}: ${number.bangla}`"
                      :aria-current="index === currentNumberIndex ? 'step' : undefined"
                      :title="`${number.digit} · ${number.english}`"
                      @click="goToNumber(index)"
                    ></button>
                  </div>
                </aside>

                <article class="single-vowel-card number-lesson-card" aria-labelledby="number-lesson-title" aria-live="polite">
                  <div class="single-vowel-topline number-lesson-topline">
                    <span class="student-eyebrow">সংখ্যা · Number {{ String(currentNumberNumber).padStart(2, '0') }}</span>
                    <span>০–৯</span>
                  </div>

                  <div class="number-lesson-main">
                    <div class="number-bengali-digit" lang="bn">{{ currentNumber.digit }}</div>

                    <div class="number-lesson-copy">
                      <span>Bangla number name</span>
                      <h1 id="number-lesson-title" ref="heading" tabindex="-1" lang="bn">{{ currentNumber.bangla }}</h1>
                      <div class="number-ipa-row"><strong>{{ currentNumber.ipa }}</strong></div>
                      <small>Romanised as “{{ currentNumber.romanisation }}”</small>
                      <p>{{ currentNumber.english }}</p>
                    </div>
                  </div>

                  <div class="pronunciation-tip number-match-tip">
                    <span class="pronunciation-tip-icon" aria-hidden="true">০↔0</span>
                    <div>
                      <span class="student-eyebrow">Match the digits</span>
                      <h2><span lang="bn">{{ currentNumber.digit }}</span> means {{ currentNumber.value }}</h2>
                      <p>The Bangla digit <strong lang="bn">{{ currentNumber.digit }}</strong> represents the same number as <strong>{{ currentNumber.value }}</strong>. Its Bangla name is <strong lang="bn">{{ currentNumber.bangla }}</strong>.</p>
                    </div>
                  </div>

                  <nav class="vowel-pagination" aria-label="Number pagination">
                    <button type="button" :disabled="currentNumberIndex === 0" aria-label="Previous number" title="Previous number" @click="showPreviousNumber">
                      <span aria-hidden="true">◀</span>
                    </button>
                    <span>{{ currentNumberNumber }}/{{ numberItems.length }}</span>
                    <button type="button" :aria-label="currentNumberIndex === numberItems.length - 1 ? 'Finish number lesson' : 'Next number'" :title="currentNumberIndex === numberItems.length - 1 ? 'Finish number lesson' : 'Next number'" @click="currentNumberIndex === numberItems.length - 1 ? finishNumberLesson() : showNextNumber()">
                      <span aria-hidden="true">▶</span>
                    </button>
                  </nav>
                </article>
              </div>
            </template>

            <template v-else-if="studentLesson === 'conversation-home'">
              <section class="conversation-chapter-home" aria-labelledby="conversation-chapter-title">
                <header class="conversation-chapter-header">
                  <div>
                    <span class="student-eyebrow">Textbook lessons</span>
                    <h1 id="conversation-chapter-title" ref="heading" tabindex="-1">Choose a chapter</h1>
                    <p>Follow conversations and stories in the same order as the Grade 2 Bangla textbook.</p>
                  </div>
                  <span class="conversation-chapter-count">{{ conversationChapters.length }} chapters</span>
                </header>

                <div class="conversation-chapter-grid">
                  <button
                    v-for="(chapter, index) in conversationChapters"
                    :key="chapter.id"
                    class="conversation-chapter-card"
                    :class="`conversation-chapter-card--${chapter.tone}`"
                    type="button"
                    @click="openConversationChapter(index)"
                  >
                    <span class="conversation-chapter-number">{{ String(chapter.number).padStart(2, '0') }}</span>
                    <span class="conversation-chapter-copy">
                      <small>Chapter {{ chapter.number }} · Textbook pages {{ chapter.sourcePages }}</small>
                      <strong lang="bn">{{ chapter.banglaTitle }}</strong>
                      <b>{{ chapter.englishTitle }}</b>
                      <span>{{ chapter.description }}</span>
                    </span>
                    <span class="conversation-chapter-meta">
                      <b>{{ chapter.lessons.length }}</b>
                      <small>{{ chapter.format === 'article' ? 'sections' : 'parts' }}</small>
                      <i aria-hidden="true">→</i>
                    </span>
                  </button>
                </div>
              </section>
            </template>

            <template v-else-if="studentLesson === 'conversations'">
              <div class="vowel-lesson-stage conversation-lesson-stage">
                <aside class="vowel-sidebar-progress consonant-progress-rail" :aria-label="`Chapter ${currentConversationChapter.number} progress: ${currentConversationNumber} of ${currentConversationLessons.length}`">
                  <span>{{ currentConversationChapter.format === 'article' ? 'Reading progress' : 'Conversation progress' }}</span>
                  <strong>{{ currentConversationNumber }} / {{ currentConversationLessons.length }}</strong>
                  <div class="consonant-dot-track" :style="{ '--lesson-steps': currentConversationLessons.length }" role="navigation" aria-label="Jump to a conversation">
                    <button
                      v-for="(conversation, index) in currentConversationLessons"
                      :key="conversation.id"
                      class="consonant-progress-dot"
                      :class="{ completed: index < currentConversationIndex, current: index === currentConversationIndex }"
                      type="button"
                      :aria-label="`${currentConversationChapter.format === 'article' ? 'Reading section' : 'Conversation'} ${index + 1}: ${conversation.scene}`"
                      :aria-current="index === currentConversationIndex ? 'step' : undefined"
                      :title="`${index + 1}. ${conversation.scene}`"
                      @click="goToConversation(index)"
                    ></button>
                  </div>
                </aside>

                <article class="single-vowel-card conversation-lesson-card" aria-labelledby="conversation-lesson-title" aria-live="polite">
                  <div class="single-vowel-topline conversation-lesson-topline">
                    <span class="student-eyebrow">Chapter {{ currentConversationChapter.number }} · {{ currentConversationChapter.format === 'article' ? 'Section' : 'Part' }} {{ currentConversationNumber }}</span>
                    <span>{{ currentConversationChapter.englishTitle }}</span>
                  </div>

                  <section v-if="currentConversationChapter.format === 'article'" id="conversation-lesson-title" ref="heading" class="story-reading-main" tabindex="-1">
                    <span class="student-eyebrow">Reading passage</span>
                    <h1 lang="bn">{{ currentConversation.banglaHeading }}</h1>
                    <div class="story-bangla-text">
                      <p v-for="paragraph in currentConversation.paragraphs" :key="paragraph.bangla" lang="bn">{{ paragraph.bangla }}</p>
                    </div>
                    <details class="story-translation">
                      <summary>English translation</summary>
                      <div>
                        <p v-for="paragraph in currentConversation.paragraphs" :key="paragraph.english">{{ paragraph.english }}</p>
                      </div>
                    </details>
                  </section>

                  <div v-else id="conversation-lesson-title" ref="heading" class="conversation-lesson-main conversation-chat-area" tabindex="-1">

                        <div
                          v-for="(line, lineIndex) in currentConversation.lines"
                          :key="`${currentConversation.id}-${line.speaker}`"
                          class="conversation-message-row"
                          :class="{ 'conversation-message-row--sent': lineIndex % 2 === 1 }"
                        >
                          <span class="conversation-message-avatar" aria-hidden="true">{{ lineIndex % 2 === 0 ? 'A' : 'B' }}</span>
                          <button
                            class="conversation-flashcard"
                            :class="{ flipped: isConversationLineFlipped(lineIndex) }"
                            type="button"
                            :aria-pressed="isConversationLineFlipped(lineIndex)"
                            :aria-label="`${isConversationLineFlipped(lineIndex) ? 'Show Bangla' : 'Show translation and pronunciation'} for ${line.bangla}`"
                            @click="toggleConversationLine(lineIndex)"
                          >
                            <span class="conversation-flashcard-inner">
                              <span class="conversation-flashcard-face conversation-flashcard-front">
                                <strong lang="bn">{{ line.bangla }}</strong>
                              </span>
                              <span class="conversation-flashcard-face conversation-flashcard-back">
                                <strong>{{ line.english }}</strong>
                                <span class="conversation-ipa">{{ line.ipa }}</span>
                                <small>Romanised as “{{ line.romanisation }}”</small>
                              </span>
                            </span>
                          </button>
                        </div>
                    <span class="conversation-card-hint">Tap to see translation</span>
                  </div>

                  <nav class="vowel-pagination" aria-label="Conversation pagination">
                    <button type="button" :disabled="currentConversationIndex === 0" aria-label="Previous conversation" title="Previous conversation" @click="showPreviousConversation">
                      <span aria-hidden="true">◀</span>
                    </button>
                    <span>{{ currentConversationNumber }}/{{ currentConversationLessons.length }}</span>
                    <button type="button" :aria-label="currentConversationIndex === currentConversationLessons.length - 1 ? 'Finish chapter' : 'Next conversation'" :title="currentConversationIndex === currentConversationLessons.length - 1 ? 'Finish chapter' : 'Next conversation'" @click="currentConversationIndex === currentConversationLessons.length - 1 ? finishConversationLesson() : showNextConversation()">
                      <span aria-hidden="true">▶</span>
                    </button>
                  </nav>
                </article>
              </div>
            </template>

            <template v-else-if="studentLesson === 'vowels'">
              <div class="vowel-lesson-stage">
                <aside class="vowel-sidebar-progress consonant-progress-rail" :aria-label="`Vowel learning progress: ${currentVowelNumber} of ${vowels.length}`">
                  <span>Vowel progress</span>
                  <strong>{{ currentVowelNumber }} / {{ vowels.length }}</strong>
                  <div class="consonant-dot-track" :style="{ '--lesson-steps': vowels.length }" role="navigation" aria-label="Jump to a vowel">
                    <button
                      v-for="(vowel, index) in vowels"
                      :key="vowel.letter"
                      class="consonant-progress-dot"
                      :class="{ completed: index < currentVowelIndex, current: index === currentVowelIndex }"
                      type="button"
                      :aria-label="`Vowel ${index + 1}: ${vowel.letter}`"
                      :aria-current="index === currentVowelIndex ? 'step' : undefined"
                      :title="`${index + 1}. ${vowel.letter} ${vowel.ipa}`"
                      @click="goToVowel(index)"
                    ></button>
                  </div>
                </aside>

                <article class="single-vowel-card" aria-labelledby="single-vowel-title" aria-live="polite">
                <div class="single-vowel-topline">
                  <span class="student-eyebrow">স্বরবর্ণ · Vowel {{ String(currentVowelNumber).padStart(2, '0') }}</span>
                </div>

                <div class="single-vowel-letter-wrap">
                  <div id="single-vowel-title" class="single-vowel-letter" lang="bn">{{ currentVowel.letter }}</div>
                  <div class="single-vowel-transcription">
                    <span>Pronunciation</span>
                    <div class="vowel-ipa-row">
                      <strong>{{ currentVowel.ipa }}</strong>
                      <button class="vowel-speaker-button" type="button" :aria-label="`Play pronunciation for ${currentVowel.letter}`" title="Play pronunciation" @click="previewVowelSound">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Zm12.5-.5a5 5 0 0 1 0 7m2.5-9.5a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>
                      </button>
                    </div>
                    <small>Romanised as “{{ currentVowel.romanisation }}”</small>
                  </div>
                </div>

                <div class="pronunciation-tip">
                  <span class="pronunciation-tip-icon" aria-hidden="true">i</span>
                  <div>
                    <span class="student-eyebrow">English pronunciation tip</span>
                    <h2>{{ currentVowel.tipTitle }}</h2>
                    <p>{{ currentVowel.tip }}</p>
                  </div>
                </div>

                <nav class="vowel-pagination" aria-label="Vowel lesson pages">
                  <button type="button" :disabled="currentVowelIndex === 0" aria-label="Previous vowel" title="Previous vowel" @click="showPreviousVowel">
                    <span class="page-triangle page-triangle--left" aria-hidden="true"></span>
                  </button>
                  <span>{{ currentVowelNumber }}/{{ vowels.length }}</span>
                  <button type="button" :aria-label="currentVowelIndex === vowels.length - 1 ? 'Finish vowel lesson' : 'Next vowel'" :title="currentVowelIndex === vowels.length - 1 ? 'Finish vowel lesson' : 'Next vowel'" @click="currentVowelIndex === vowels.length - 1 ? finishVowelLesson() : showNextVowel()">
                    <span class="page-triangle page-triangle--right" aria-hidden="true"></span>
                  </button>
                </nav>
                </article>
              </div>

              <p v-if="vowelFeedback" class="vowel-feedback" role="status">{{ vowelFeedback }}</p>
            </template>

            <template v-else-if="studentLesson === 'consonants'">
              <div class="vowel-lesson-stage consonant-lesson-stage">
                <aside class="vowel-sidebar-progress consonant-progress-rail" :aria-label="`Consonant learning progress: ${currentConsonantNumber} of ${consonants.length}`">
                  <span>Consonant progress</span>
                  <strong>{{ currentConsonantNumber }} / {{ consonants.length }}</strong>
                  <div class="consonant-dot-track" :style="{ '--lesson-steps': consonants.length }" role="navigation" aria-label="Jump to a consonant">
                    <button
                      v-for="(consonant, index) in consonants"
                      :key="consonant.letter"
                      class="consonant-progress-dot"
                      :class="{ completed: index < currentConsonantIndex, current: index === currentConsonantIndex }"
                      type="button"
                      :aria-label="`Consonant ${index + 1}: ${consonant.letter}`"
                      :aria-current="index === currentConsonantIndex ? 'step' : undefined"
                      :title="`${index + 1}. ${consonant.letter} ${consonant.ipa}`"
                      @click="goToConsonant(index)"
                    ></button>
                  </div>
                </aside>

                <article class="single-vowel-card consonant-card" aria-labelledby="single-consonant-title" aria-live="polite">
                <div class="single-vowel-topline">
                  <span class="student-eyebrow">
                    {{ currentConsonant.category === 'special' ? 'বিশেষ চিহ্ন · Special sign' : 'ব্যঞ্জনবর্ণ · Consonant' }}
                    {{ String(currentConsonantNumber).padStart(2, '0') }}
                  </span>
                </div>

                <div class="single-vowel-letter-wrap">
                  <div id="single-consonant-title" class="single-vowel-letter" :class="{ 'special-sign-display': currentConsonant.category === 'special' }" lang="bn">{{ currentConsonantCombination }}</div>
                  <div class="single-vowel-transcription">
                    <span>Pronunciation</span>
                    <div class="vowel-ipa-row">
                      <strong>{{ currentConsonantCombinationIpa }}</strong>
                      <button class="vowel-speaker-button" type="button" :aria-label="`Play pronunciation for ${currentConsonantCombination}`" title="Play pronunciation" @click="previewConsonantSound">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Zm12.5-.5a5 5 0 0 1 0 7m2.5-9.5a8 8 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>
                      </button>
                    </div>
                    <small>Romanised as “{{ currentConsonantCombinationRomanisation }}”</small>
                    <p v-if="currentConsonantCanBlend" class="consonant-inherent-note">
                      <template v-if="currentConsonantVowelIndex === 0">
                        <b>Built-in অ /ɔ/:</b>
                        {{ currentConsonant.letter }} is read /{{ currentConsonantSpokenIpa }}/ (“{{ currentConsonantCombinationRomanisation }}”), not /{{ currentConsonantBaseIpa }}/.
                      </template>
                      <template v-else>
                        <b>With {{ currentConsonantVowel.vowel }}:</b>
                        {{ currentConsonant.letter }} + {{ currentConsonantVowel.signName }} becomes {{ currentConsonantCombination }}, read /{{ currentConsonantSpokenIpa }}/.
                      </template>
                    </p>
                  </div>
                </div>

                <div v-if="currentConsonantCanBlend" class="consonant-vowel-picker" aria-label="Choose a vowel for this consonant">
                  <span>Choose a vowel</span>
                  <div>
                    <button
                      v-for="(vowel, index) in consonantVowels"
                      :key="vowel.vowel"
                      type="button"
                      :class="{ selected: currentConsonantVowelIndex === index }"
                      :aria-pressed="currentConsonantVowelIndex === index"
                      :title="vowel.signName"
                      @click="selectConsonantVowel(index)"
                    >
                      <span lang="bn">{{ vowel.vowel }}</span>
                    </button>
                  </div>
                </div>

                <div class="pronunciation-tip">
                  <span class="pronunciation-tip-icon" aria-hidden="true">i</span>
                  <div>
                    <span class="student-eyebrow">English pronunciation tip</span>
                    <h2>{{ currentConsonant.tipTitle }}</h2>
                    <p>{{ currentConsonant.tip }}</p>
                  </div>
                </div>

                <nav class="vowel-pagination" aria-label="Consonant lesson pages">
                  <button type="button" :disabled="currentConsonantIndex === 0" aria-label="Previous consonant" title="Previous consonant" @click="showPreviousConsonant">
                    <span class="page-triangle page-triangle--left" aria-hidden="true"></span>
                  </button>
                  <span>{{ currentConsonantNumber }}/{{ consonants.length }}</span>
                  <button type="button" :aria-label="currentConsonantIndex === consonants.length - 1 ? 'Finish consonant lesson' : 'Next consonant'" :title="currentConsonantIndex === consonants.length - 1 ? 'Finish consonant lesson' : 'Next consonant'" @click="currentConsonantIndex === consonants.length - 1 ? finishConsonantLesson() : showNextConsonant()">
                    <span class="page-triangle page-triangle--right" aria-hidden="true"></span>
                  </button>
                </nav>
                </article>
              </div>

              <p v-if="consonantFeedback" class="vowel-feedback" role="status">{{ consonantFeedback }}</p>
            </template>
          </section>
          <form v-else-if="isChildCreate" class="child-profile-form" novalidate @submit.prevent="submitChildProfile">
            <fieldset>
              <label for="child-nickname">Child’s nickname</label>
              <input id="child-nickname" v-model="childNickname" type="text" autocomplete="off" maxlength="60" placeholder="Enter a nickname" required :aria-invalid="!!fieldErrors.nickname" :aria-describedby="fieldErrors.nickname ? 'nickname-error' : undefined" @input="clearFieldError('nickname')">
              <p v-if="fieldErrors.nickname" id="nickname-error" class="field-error" role="alert">{{ fieldErrors.nickname }}</p>

              <fieldset class="avatar-fieldset" :aria-describedby="fieldErrors.avatar ? 'avatar-error avatar-hint' : 'avatar-hint'">
                <legend>Choose an avatar</legend>
                <div class="profile-avatar-options" role="radiogroup" aria-label="Choose an avatar">
                  <button v-for="avatar in avatarChoices" :key="avatar.id" class="profile-avatar-choice" :class="{ selected: selectedAvatar === avatar.id }" type="button" role="radio" :aria-checked="selectedAvatar === avatar.id" :aria-label="avatar.label" @click="selectAvatar(avatar.id)">
                    <img :src="avatar.src" alt="">
                    <span v-if="selectedAvatar === avatar.id" class="avatar-check" aria-hidden="true">✓</span>
                  </button>
                  <label class="profile-avatar-choice upload-avatar-choice" :class="{ selected: selectedAvatar === 'custom' }" :title="customAvatarName || 'Upload your own'">
                    <input class="sr-only" type="file" accept="image/png,image/jpeg,image/webp" @change="uploadAvatar">
                    <img v-if="customAvatarUrl" :src="customAvatarUrl" alt="Custom avatar preview">
                    <svg v-else viewBox="0 0 64 64" aria-hidden="true"><path d="M17 20h8l3-5h9l3 5h7a6 6 0 0 1 6 6v20a6 6 0 0 1-6 6H17a6 6 0 0 1-6-6V26a6 6 0 0 1 6-6Z" fill="currentColor" opacity=".2"/><circle cx="32" cy="36" r="9" fill="none" stroke="currentColor" stroke-width="4"/><path d="M49 11v12m-6-6h12" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg>
                    <span class="upload-label">Upload your own</span>
                    <span v-if="selectedAvatar === 'custom'" class="avatar-check" aria-hidden="true">✓</span>
                  </label>
                </div>
                <p id="avatar-hint" class="field-hint">PNG, JPG, or WebP · up to 2 MB.</p>
                <p v-if="fieldErrors.avatar" id="avatar-error" class="field-error" role="alert">{{ fieldErrors.avatar }}</p>
              </fieldset>

              <label for="child-age-band">Age group</label>
              <select id="child-age-band" v-model="childAgeBand" required :aria-invalid="!!fieldErrors.ageBand" :aria-describedby="fieldErrors.ageBand ? 'age-band-error' : 'age-band-hint'" @change="clearFieldError('ageBand')">
                <option value="junior">Junior learner</option>
                <option value="senior">Senior learner</option>
              </select>
              <p id="age-band-hint" class="field-hint">The age group determines the child’s starting learning content.</p>
              <p v-if="fieldErrors.ageBand" id="age-band-error" class="field-error" role="alert">{{ fieldErrors.ageBand }}</p>

              <div class="child-form-actions">
                <button class="secondary" type="button" @click="cancelChildCreate">Cancel</button>
                <button class="primary" type="submit">{{ isChildEdit ? 'Save changes' : 'Create profile' }} <span aria-hidden="true">→</span></button>
              </div>
            </fieldset>
          </form>
          <div v-else-if="childrenLoading" class="notice" role="status">Loading child profiles…</div>
          <section v-else-if="children.length" aria-label="Your child profiles">
            <div class="family-meta">
              <span>Your child profiles</span>
              <span>{{ children.length }} of 5 profiles</span>
            </div>
            <div class="profile-grid">
              <article v-for="child in children" :key="child.childID" class="profile-card">
                <img class="profile-avatar-image" :class="{ custom: isCustomAvatar(child.avatar) }" :src="avatarSource(child.avatar)" alt="">
                <strong>{{ child.nickname }}</strong>
                <small>{{ child.ageBand === 'senior' ? 'Senior learner' : 'Junior learner' }}<template v-if="child.levelTitle"> · {{ child.levelTitle }}</template></small>
                <button class="profile-learn-button" type="button" :aria-label="`Open ${child.nickname}'s student homepage`" @click="openStudentHome(child)">Start learning <span aria-hidden="true">→</span></button>
                <div class="profile-card-actions">
                  <button class="profile-edit-button" type="button" :aria-label="`Edit ${child.nickname}'s profile`" @click="openChildEdit(child)">Edit</button>
                  <button class="profile-delete-button" type="button" :aria-label="`Delete ${child.nickname}'s profile`" @click="openDeleteConfirm(child.childID)">Delete</button>
                </div>
                <div v-if="deleteConfirmId === child.childID" class="profile-delete-confirm" role="alert">
                  <p>Delete {{ child.nickname }}’s profile? This cannot be undone.</p>
                  <template v-if="!deleteChallenge">
                    <p>A verification code will be sent to {{ signedIn.email }}.</p>
                    <div>
                      <button class="danger" type="button" :disabled="busy" @click="requestDeleteCode(child)">Send code</button>
                      <button class="secondary" type="button" :disabled="busy" @click="cancelDeleteConfirm">Cancel</button>
                    </div>
                  </template>
                  <template v-else>
                    <label :for="`delete-code-${child.childID}`">6-digit verification code</label>
                    <input :id="`delete-code-${child.childID}`" v-model="deleteCode" class="delete-code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" :aria-invalid="!!fieldErrors.deleteCode" :aria-describedby="fieldErrors.deleteCode ? `delete-code-error-${child.childID}` : undefined" @input="clearFieldError('deleteCode')">
                    <p v-if="fieldErrors.deleteCode" :id="`delete-code-error-${child.childID}`" class="field-error" role="alert">{{ fieldErrors.deleteCode }}</p>
                    <p class="delete-code-hint">Valid for 10 minutes. Up to 5 attempts.</p>
                    <div class="delete-resend-row">
                      <button class="text-button" type="button" :disabled="deleteCooldown > 0 || busy" @click="resendDeleteCode">{{ deleteCooldown > 0 ? `Resend in ${deleteCooldown}s` : 'Resend code' }}</button>
                    </div>
                    <div>
                      <button class="danger" type="button" :disabled="busy" @click="confirmDeleteChild(child)">Verify & delete</button>
                      <button class="secondary" type="button" :disabled="busy" @click="cancelDeleteConfirm">Cancel</button>
                    </div>
                  </template>
                </div>
              </article>
              <button v-if="children.length < 5" class="add-profile" type="button" @click="openChildCreate">
                <span aria-hidden="true">＋</span>
                <strong>Add child profile</strong>
                <small>{{ 5 - children.length }} {{ 5 - children.length === 1 ? 'place' : 'places' }} remaining</small>
              </button>
            </div>
          </section>
          <div v-else class="child-empty-state">
            <svg class="child-empty-icon" viewBox="0 0 72 82" aria-hidden="true">
              <path d="M36 30V16" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/>
              <path d="M35 20C19 21 14 10 15 3C28 2 37 8 35 20ZM38 18C39 7 49 2 59 5C59 15 50 22 38 18Z" fill="currentColor" opacity=".78"/>
              <circle cx="36" cy="51" r="25" fill="currentColor" opacity=".16"/>
              <path d="M25 49c1-4 6-4 7 0m8 0c1-4 6-4 7 0M28 59c5 6 12 6 17 0" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"/>
            </svg>
            <h2>No child profiles yet.</h2>
            <p>Add a child profile to get started.</p>
            <button class="primary add-child-button" type="button" @click="openChildCreate">Add child profile <span aria-hidden="true">→</span></button>
          </div>
        </template>
        <form v-else novalidate @submit.prevent="submit"><fieldset :disabled="busy">
          <template v-if="['login', 'register', 'forgot'].includes(page)"><label for="email">Email address</label><input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com" required maxlength="254" :aria-invalid="!!fieldErrors.email" :aria-describedby="fieldErrors.email ? 'email-error' : undefined" @input="clearFieldError('email')"><p v-if="fieldErrors.email" id="email-error" class="field-error" role="alert">{{ fieldErrors.email }}</p></template>
          <template v-if="['login', 'register', 'reset'].includes(page)"><label for="password">{{ page === 'reset' ? 'New password' : 'Password' }}</label><div class="password-field"><input id="password" v-model="password" type="password" :autocomplete="page === 'login' ? 'current-password' : 'new-password'" :placeholder="page === 'reset' ? 'Enter your new password' : 'Enter your password'" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.password" :aria-describedby="fieldErrors.password ? 'password-error' : undefined" @input="clearFieldError('password')"></div><p v-if="fieldErrors.password" id="password-error" class="field-error" role="alert">{{ fieldErrors.password }}</p><button v-if="page === 'login'" class="text-button forgot" type="button" @click="go('forgot')">Forgot password?</button><p v-if="page !== 'login'" class="field-hint">Use 8–128 characters.</p></template>
          <template v-if="['register', 'reset'].includes(page)"><label for="confirm">{{ page === 'reset' ? 'Confirm new password' : 'Confirm password' }}</label><input id="confirm" v-model="confirm" type="password" autocomplete="new-password" :placeholder="page === 'reset' ? 'Enter your new password again' : 'Enter your password again'" required minlength="8" maxlength="128" :aria-invalid="!!fieldErrors.confirm" :aria-describedby="fieldErrors.confirm ? 'confirm-error' : undefined" @input="clearFieldError('confirm')"><p v-if="fieldErrors.confirm" id="confirm-error" class="field-error" role="alert">{{ fieldErrors.confirm }}</p></template>
          <template v-if="page === 'verify'"><div class="email-summary">Verification for <strong>{{ email }}</strong></div><label for="code">6-digit verification code</label><input id="code" v-model="code" class="code-input" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required :aria-invalid="!!fieldErrors.code" :aria-describedby="fieldErrors.code ? 'code-error code-hint' : 'code-hint'" @input="clearFieldError('code')"><p v-if="fieldErrors.code" id="code-error" class="field-error" role="alert">{{ fieldErrors.code }}</p><p id="code-hint" class="field-hint">Valid for 10 minutes. Up to 5 attempts.</p><div v-if="challenge?.delivery === 'development'" class="development-code">Local development code: <strong>{{ challenge.development_code }}</strong><br>No email was sent.</div></template>
          <button class="primary submit-button" type="submit">{{ busy ? 'Please wait…' : ({ login: 'Continue', register: 'Create account', forgot: 'Send verification code', verify: 'Verify & continue', reset: 'Reset password' })[page] }} <span v-if="!busy" aria-hidden="true">→</span></button>
          <button v-if="page === 'forgot'" class="back-button" type="button" @click="go('login')">← Back to log in</button>
          <div v-if="page === 'verify'" class="resend-row"><span>Need another code?</span><button class="text-button" type="button" :disabled="cooldown > 0 || busy" @click="resend">{{ cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend code' }}</button></div><button v-if="page === 'verify'" class="back-button" type="button" @click="go('login')">← Back to log in</button>
        </fieldset></form>
      </template>
      <footer class="account-footer" :class="{ 'student-footer': isStudentHome }"><div class="sprout-divider" aria-hidden="true"><span></span><svg viewBox="0 0 32 32"><path d="M16 27V15" stroke="currentColor" stroke-width="2"/><path d="M15 21C4 22 2 13 3 7C12 6 17 12 15 21M17 18C17 8 24 5 29 6C30 15 24 21 17 18" fill="currentColor"/></svg><span></span></div><p v-if="!isStudentHome">A parent account. A shared adventure.</p></footer>
      <p v-if="developmentCodes && !isStudentHome" class="development-note">Local development · Email verification uses an on-screen code.</p>
    </section>
    <div v-if="completedLesson" class="vowel-completion-celebration" role="status" aria-live="polite">
      <div class="firework firework--one" aria-hidden="true"><span v-for="spark in 12" :key="`one-${spark}`" :style="{ '--spark': spark - 1 }"></span></div>
      <div class="firework firework--two" aria-hidden="true"><span v-for="spark in 12" :key="`two-${spark}`" :style="{ '--spark': spark - 1 }"></span></div>
      <div class="firework firework--three" aria-hidden="true"><span v-for="spark in 12" :key="`three-${spark}`" :style="{ '--spark': spark - 1 }"></span></div>
      <div class="vowel-completion-message">
        <span aria-hidden="true">✓</span>
        <strong>Congratulations!</strong>
        <p>You have completed the {{ completedLesson }} section.</p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.account-page {
  background: #fff;
  --signed-content-top-gap: clamp(60px, 7.5svh, 86px);
  --signed-page-width: 1180px;
}

input[aria-invalid='true'] {
  border-color: #b44435;
  box-shadow: 0 0 0 3px #b4443518;
}

.field-error {
  color: #b44435;
  font-size: 14px;
  font-weight: 700;
  margin: 7px 0 0;
}

.account-session {
  align-items: center;
  background: #174b39;
  box-shadow: 0 10px 24px rgba(23, 75, 57, .2);
  box-sizing: border-box;
  color: #fff;
  display: flex;
  justify-content: space-between;
  margin-left: calc(50% - 50vw);
  margin-bottom: 54px;
  min-height: 82px;
  padding: 14px 28px;
  width: 100vw;
}

.account-session strong {
  font-size: 15px;
  overflow-wrap: anywhere;
}

.account-session-pin,
.account-session-user {
  align-items: center;
  display: flex;
  gap: 18px;
}

.account-session .text-button {
  color: #fff;
  font-size: 15px;
  padding: 8px 12px;
}

.account-session-user .text-button {
  border-left: 1px solid rgba(255, 255, 255, .35);
  border-radius: 0;
  padding-left: 24px;
}

.pin-status {
  color: #c9d9d1;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.account-page.signed-in-page {
  align-items: flex-start;
  overflow-x: clip;
  padding-top: 0;
}

.account-nav-back {
  font-weight: 750;
}

.pin-editor {
  background: #f5f8f0;
  border: 1px solid #c8d5ba;
  border-radius: 18px;
  margin-bottom: 30px;
  padding: 24px;
}

.pin-editor h2 {
  margin-bottom: 6px;
}

.pin-editor-icon {
  align-items: center;
  background: #e7f0df;
  border: 2px solid #c8d8bd;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  height: 92px;
  justify-content: center;
  margin: 0 auto 18px;
  width: 92px;
}

.pin-editor-icon svg {
  height: 58px;
  width: 52px;
}

.pin-editor > fieldset > p:not(.field-error) {
  color: #6c7f65;
  margin: 0 0 20px;
}

.pin-editor label {
  margin-top: 16px;
}

.pin-editor input {
  font-size: 24px;
  letter-spacing: 9px;
  text-align: center;
}

.pin-editor-actions {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr;
  margin-top: 24px;
}

.parent-pin-gate {
  background: #f5f8f0;
  border: 1px solid #c8d5ba;
  border-radius: 18px;
  padding: 28px;
}

.parent-pin-gate label {
  margin-top: 0;
}

.parent-pin-gate input {
  font-size: 26px;
  letter-spacing: 10px;
  text-align: center;
}

.parent-dashboard-placeholder {
  align-items: center;
  background: #edf3e5;
  border: 1px solid #c8d5ba;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  padding: 46px 28px;
  text-align: center;
}

.parent-dashboard-placeholder > div {
  align-items: center;
  background: #2c6248;
  border-radius: 50%;
  color: white;
  display: flex;
  font-size: 28px;
  height: 58px;
  justify-content: center;
  margin-bottom: 18px;
  width: 58px;
}

.parent-dashboard-placeholder p {
  color: #5e7165;
  margin: 0 0 24px;
  max-width: 440px;
}

.child-empty-state {
  align-items: center;
  background: #edf3e5;
  border: 1px solid #c8d5ba;
  border-radius: 24px;
  color: #174b39;
  display: flex;
  flex-direction: column;
  margin-top: 42px;
  padding: 48px 32px;
  text-align: center;
}

.child-empty-icon {
  height: 82px;
  margin-bottom: 18px;
  width: 72px;
}

.child-empty-state h2 {
  font-size: clamp(28px, 4vw, 38px);
  margin: 0 0 12px;
}

.child-empty-state p {
  color: #42566b;
  font-size: 20px;
  margin: 0 0 28px;
}

.add-child-button {
  max-width: 430px;
  width: 100%;
}

.child-back-button {
  background: none;
  border: 0;
  color: #2c6248;
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 26px;
  min-height: 44px;
  padding: 8px 0;
}

.child-profile-form {
  margin-top: 4px;
}

.avatar-fieldset {
  margin-top: 25px;
}

.avatar-fieldset legend {
  margin: 0 0 12px;
}

.profile-avatar-options {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.profile-avatar-choice {
  align-items: center;
  aspect-ratio: 1;
  background: #f3f6ed;
  border: 2px solid transparent;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  justify-content: center;
  margin: 0;
  min-width: 0;
  padding: 8px;
  position: relative;
}

button.profile-avatar-choice {
  width: 100%;
}

.profile-avatar-choice:hover,
.profile-avatar-choice.selected {
  border-color: #547963;
}

.profile-avatar-choice img {
  height: 100%;
  object-fit: contain;
  width: 100%;
}

.avatar-check {
  align-items: center;
  background: #2c6248;
  border: 2px solid #fcfcf8;
  border-radius: 50%;
  color: #fff;
  display: flex;
  font-size: 14px;
  font-weight: 800;
  height: 26px;
  justify-content: center;
  position: absolute;
  right: -3px;
  top: -3px;
  width: 26px;
}

.upload-avatar-choice {
  cursor: pointer;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
  text-align: center;
}

.upload-avatar-choice svg {
  height: 43%;
  width: 43%;
}

.upload-avatar-choice img {
  border-radius: 50%;
  inset: 0;
  object-fit: cover;
  position: absolute;
}

.upload-label {
  font-size: 11px;
  font-weight: 700;
  line-height: 1.05;
}

.child-form-actions {
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr 1fr;
  margin-top: 30px;
}

.child-form-actions button {
  min-height: 56px;
}

.child-form-actions .primary {
  align-items: center;
  display: flex;
  gap: 18px;
  justify-content: center;
}

.profile-card {
  align-items: center;
  background: #f3f6ed;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 200px;
  transition: box-shadow .2s ease, transform .2s ease;
}

.profile-card:hover,
.profile-card:focus-within {
  box-shadow: 0 14px 28px rgba(36, 71, 59, .12);
  transform: translateY(-3px);
}

.profile-avatar-image {
  background: #f3f6ed;
  border: 2px solid #cbd8c7;
  border-radius: 50%;
  height: 104px;
  object-fit: contain;
  padding: 7px;
  width: 104px;
}

.profile-avatar-image.custom {
  object-fit: cover;
  padding: 0;
}

.profile-card strong {
  font-size: 18px;
  overflow-wrap: anywhere;
}

.profile-card small {
  color: #72816a;
  font-size: 14px;
}

.profile-learn-button {
  background: #2c513e;
  border: 1px solid #2c513e;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  font-weight: 750;
  margin-top: 8px;
  min-height: 44px;
  padding: 10px 18px;
  width: 100%;
}

.profile-learn-button:hover:not(:disabled) {
  background: #203f30;
}

.student-home {
  display: grid;
  gap: 30px;
  min-width: 0;
  position: relative;
}

.student-home-content {
  display: grid;
  gap: 24px;
  min-width: 0;
  width: 100%;
}

.student-footer {
  margin-top: 52px;
}

.student-eyebrow {
  color: #66815b;
  display: block;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .08em;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.account-page.student-page {
  align-items: flex-start;
  overflow-x: clip;
  overflow-y: visible;
  padding-left: 0;
  padding-right: 0;
  padding-top: 28px;
}

.account-content.student-content {
  max-width: none;
  min-width: 0;
  width: 100%;
}

.student-nav {
  align-items: center;
  background: #174b39;
  box-shadow: 0 10px 24px rgba(23, 75, 57, .2);
  box-sizing: border-box;
  display: flex;
  justify-content: space-between;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  margin-top: -28px;
  min-height: 82px;
  padding: 14px 28px;
  width: 100vw;
}

.student-home-content,
.student-content .blending-group-page,
.student-lesson-content .vowel-lesson-stage,
.student-footer {
  margin-left: auto;
  margin-right: auto;
  max-width: var(--signed-page-width);
  width: calc(100% - 48px);
}

.student-brand {
  align-items: center;
  background: transparent;
  border: 0;
  color: #fff;
  display: flex;
  gap: 12px;
  padding: 0;
  text-align: left;
}

.student-brand-mark {
  align-items: center;
  background: #dcebd3;
  color: #174b39;
  border-radius: 14px;
  display: flex;
  font-size: 26px;
  font-weight: 850;
  height: 52px;
  justify-content: center;
  width: 52px;
}

.student-brand > span:last-child,
.student-nav-account > div {
  display: flex;
  flex-direction: column;
}

.student-brand strong {
  font-size: 15px;
}

.student-brand small,
.student-nav-account small {
  color: #c9d9d1;
  font-size: 15px;
}

.student-nav-account {
  align-items: center;
  display: flex;
  gap: 6px;
}

.student-nav-avatar {
  background: #f3f6ed;
  border: 2px solid #cbd8c7;
  border-radius: 50%;
  flex: 0 0 42px;
  height: 42px;
  object-fit: contain;
  padding: 3px;
  width: 42px;
}

.student-nav-avatar.custom {
  object-fit: cover;
  padding: 0;
}

.student-nav-account > .student-identity {
  align-items: center;
  flex-direction: row;
  gap: 9px;
  min-width: 0;
}

.student-nav-account strong {
  color: #fff;
  font-size: 15px;
  overflow-wrap: anywhere;
}

.student-signout {
  background: transparent;
  border: 0;
  border-left: 1px solid rgba(255, 255, 255, .35);
  border-radius: 0;
  color: #fff;
  font-size: 15px;
  font-weight: 750;
  min-height: 44px;
  margin-left: 6px;
  padding: 8px 8px 8px 18px;
}

.student-signout:hover:not(:disabled) {
  background: transparent;
  text-decoration: underline;
}

.learning-preview {
  background: #e8f3f4;
  border: 1px solid #c4dfe0;
  border-radius: 14px;
  color: #2e5a58;
  margin: -10px 0 0;
  padding: 13px 16px;
}

.student-welcome {
  align-items: start;
  background: linear-gradient(135deg, #edf5e7 0%, #f8f2dc 100%);
  border: 1px solid #cbd9be;
  border-radius: 28px;
  display: grid;
  gap: 24px;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: auto 1fr;
  min-height: 310px;
  padding: 36px 40px;
}

.student-welcome-copy {
  align-self: start;
}

.student-welcome-animation-space {
  grid-column: 1 / -1;
  min-height: 92px;
}

.student-welcome h1 {
  color: #174b39;
  font-size: clamp(32px, 4vw, 48px);
  line-height: 1.08;
  margin: 0 0 10px;
  max-width: 680px;
}

.student-welcome p {
  color: #52675e;
  font-size: 17px;
  margin: 0;
}

.student-level-pill {
  background: rgba(255, 255, 255, .78);
  border: 1px solid rgba(190, 207, 177, .85);
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  min-width: 170px;
  padding: 16px 20px;
}

.student-level-pill span {
  color: #72816a;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.student-level-pill strong {
  color: #174b39;
  font-size: 18px;
  margin-top: 3px;
}

.learning-area-heading {
  align-items: end;
  display: flex;
  justify-content: space-between;
}

.learning-area-heading h2 {
  color: #174b39;
  font-size: 28px;
  margin: 0;
}

.learning-area-heading > span {
  color: #6c7f65;
  font-size: 14px;
}

.learning-area-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  min-width: 0;
}

.learning-area-card {
  align-items: center;
  border: 1px solid;
  border-radius: 24px;
  color: #24473b;
  display: grid;
  gap: 18px;
  grid-template-columns: 112px minmax(0, 1fr) 40px;
  min-width: 0;
  min-height: 180px;
  padding: 24px;
  text-align: left;
  transition: box-shadow .2s ease, transform .2s ease;
}

.learning-area-card:hover {
  box-shadow: 0 14px 28px rgba(36, 71, 59, .12);
  transform: translateY(-3px);
}

.learning-area-card--mint {
  background: #edf6e8;
  border-color: #c8ddbf;
}

.learning-area-card--sun {
  background: #fbf2d9;
  border-color: #ead8a8;
}

.learning-area-card--sky {
  background: #e8f3f4;
  border-color: #c4dfe0;
}

.learning-area-card--peach {
  background: #faece3;
  border-color: #ebcebc;
}

.learning-area-symbol {
  align-items: center;
  background: rgba(255, 255, 255, .8);
  border-radius: 22px;
  display: flex;
  flex-shrink: 0;
  font-size: 26px;
  font-weight: 800;
  height: 88px;
  justify-content: center;
  letter-spacing: 0;
  line-height: 1;
  white-space: nowrap;
  width: 112px;
}

.learning-area-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.learning-area-copy small {
  color: #6c7f65;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.learning-area-copy strong {
  color: #174b39;
  font-size: 23px;
  margin: 4px 0 7px;
}

.learning-area-copy > span {
  color: #5f7069;
  font-size: 14px;
  line-height: 1.45;
}

.learning-area-arrow {
  align-items: center;
  background: rgba(255, 255, 255, .75);
  border-radius: 50%;
  display: flex;
  font-size: 22px;
  height: 40px;
  justify-content: center;
  justify-self: end;
  width: 40px;
}

.quiz-launcher {
  display: grid;
  gap: 16px;
  padding-top: 6px;
}

.quiz-launcher-grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.quiz-launcher-card {
  align-items: center;
  background: #f4f0fa;
  border: 1px solid #d8cae8;
  border-radius: 20px;
  display: flex;
  gap: 18px;
  justify-content: space-between;
  padding: 20px 22px;
}

.quiz-launcher-card > div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.quiz-launcher-card small,
.quiz-launcher-card span {
  color: #6c6178;
  font-size: 12px;
}

.quiz-launcher-card strong {
  color: #3f2857;
  font-size: 18px;
  margin: 3px 0 5px;
}

.quiz-launcher-card button {
  background: #60417b;
  border: 0;
  border-radius: 12px;
  color: #fff;
  flex: 0 0 auto;
  font-weight: 800;
  min-height: 44px;
  padding: 11px 14px;
}

.quiz-launcher-card button:disabled {
  background: #9485a0;
}

.quiz-page {
  display: grid;
  gap: 22px;
  margin: calc(var(--signed-content-top-gap) - 24px) auto 0;
  max-width: 980px;
  padding: 0 24px 80px;
  width: 100%;
}

.quiz-header {
  align-items: center;
  background: linear-gradient(135deg, #edf5e7, #f4f0fa);
  border: 1px solid #cbd9be;
  border-radius: 24px;
  display: flex;
  gap: 24px;
  justify-content: space-between;
  padding: 26px 30px;
}

.quiz-header h1 {
  color: #174b39;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.08;
  margin: 4px 0 7px;
}

.quiz-header p {
  color: #52675e;
  margin: 0;
}

.quiz-progress-pill {
  background: rgba(255, 255, 255, .82);
  border: 1px solid #c7d5c0;
  border-radius: 18px;
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  min-width: 130px;
  padding: 14px 18px;
  text-align: center;
}

.quiz-progress-pill span {
  color: #6c7f65;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
}

.quiz-progress-pill strong {
  color: #174b39;
  font-size: 24px;
}

.quiz-form fieldset,
.quiz-results {
  display: grid;
  gap: 18px;
}

.quiz-question,
.quiz-feedback,
.quiz-history {
  background: #fff;
  border: 1px solid #d7dfd2;
  border-radius: 20px;
  padding: 24px;
}

.quiz-question-title {
  align-items: flex-start;
  display: flex;
  gap: 14px;
}

.quiz-question-title > span,
.quiz-feedback-number {
  align-items: center;
  background: #e7f0df;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  flex: 0 0 36px;
  font-size: 13px;
  font-weight: 850;
  height: 36px;
  justify-content: center;
}

.quiz-question h2,
.quiz-feedback h2,
.quiz-history h2 {
  color: #24473b;
  font-size: 20px;
  margin: 5px 0 16px;
}

.quiz-question-title small {
  color: #6c7f65;
  display: block;
  margin: -10px 0 12px;
}

.quiz-options {
  display: grid;
  gap: 10px;
  margin-left: 50px;
}

.quiz-options label {
  align-items: center;
  background: #f7f9f4;
  border: 1px solid #d5ded0;
  border-radius: 14px;
  cursor: pointer;
  display: flex;
  font-size: 17px;
  gap: 12px;
  margin: 0;
  padding: 14px 16px;
}

.quiz-options label.selected {
  background: #eaf3e4;
  border-color: #7da66e;
  box-shadow: 0 0 0 2px rgba(125, 166, 110, .18);
}

.quiz-options input {
  accent-color: #2c6248;
  min-height: 18px;
  padding: 0;
  width: 18px;
}

.quiz-submit-row,
.quiz-result-actions {
  align-items: center;
  display: flex;
  gap: 16px;
  justify-content: space-between;
}

.quiz-submit-row > span {
  color: #5f7069;
  font-weight: 700;
}

.quiz-result-banner {
  align-items: center;
  background: #fbf2d9;
  border: 1px solid #ead8a8;
  border-radius: 20px;
  display: flex;
  gap: 16px;
  padding: 22px 24px;
}

.quiz-result-banner.passed {
  background: #edf6e8;
  border-color: #bcd8b0;
}

.quiz-result-banner > span {
  align-items: center;
  background: #fff;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  flex: 0 0 48px;
  font-size: 24px;
  font-weight: 900;
  height: 48px;
  justify-content: center;
}

.quiz-result-banner strong {
  color: #24473b;
  font-size: 22px;
}

.quiz-result-banner p,
.quiz-feedback p {
  color: #5f7069;
  margin: 4px 0 0;
}

.quiz-feedback-list {
  display: grid;
  gap: 12px;
}

.quiz-feedback {
  display: grid;
  gap: 14px;
  grid-template-columns: 36px minmax(0, 1fr) auto;
}

.quiz-feedback.correct {
  border-color: #a9cca0;
}

.quiz-feedback > strong {
  color: #a04b38;
  font-size: 13px;
}

.quiz-feedback.correct > strong {
  color: #39734b;
}

.quiz-history {
  display: grid;
  gap: 14px;
}

.quiz-history ol {
  display: grid;
  gap: 8px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.quiz-history li {
  align-items: center;
  background: #f7f9f4;
  border-radius: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: 1fr auto 130px;
  padding: 11px 14px;
}

.quiz-history li small {
  color: #6c7f65;
  text-align: right;
}

.spelling-module-home {
  align-self: center;
  display: grid;
  gap: 22px;
  width: 100%;
}

.spelling-module-header {
  align-items: center;
  background: linear-gradient(135deg, #e8f3f4 0%, #f8f2dc 100%);
  border: 1px solid #c8d9d2;
  border-radius: 28px;
  display: flex;
  justify-content: space-between;
  padding: 34px 40px;
}

.spelling-module-header h1 {
  color: #174b39;
  font-size: clamp(32px, 4vw, 46px);
  line-height: 1.08;
  margin: 5px 0 8px;
}

.spelling-module-header p {
  color: #52675e;
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
}

.spelling-module-count {
  background: rgba(255, 255, 255, .82);
  border: 1px solid #c8d9d2;
  border-radius: 999px;
  color: #55715f;
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 800;
  margin-left: 24px;
  padding: 12px 18px;
}

.spelling-module-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.spelling-module-card {
  align-items: center;
  border: 1px solid;
  border-radius: 26px;
  color: #24473b;
  display: grid;
  gap: 22px;
  grid-template-columns: 128px minmax(0, 1fr) 48px;
  min-height: 230px;
  padding: 30px;
  text-align: left;
  transition: box-shadow .2s ease, transform .2s ease;
}

.spelling-module-card:hover {
  box-shadow: 0 16px 32px rgba(36, 71, 59, .13);
  transform: translateY(-4px);
}

.spelling-module-card--words {
  background: #e8f3f4;
  border-color: #c4dfe0;
}

.spelling-module-card--numbers {
  background: #fbf2d9;
  border-color: #ead8a8;
}

.spelling-module-symbol {
  align-items: center;
  background: rgba(255, 255, 255, .82);
  border-radius: 24px;
  display: flex;
  font-size: 34px;
  font-weight: 800;
  height: 104px;
  justify-content: center;
  line-height: 1;
  white-space: nowrap;
  width: 128px;
}

.spelling-module-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.spelling-module-copy small {
  color: #6c7f65;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.spelling-module-copy strong {
  color: #174b39;
  font-size: 28px;
  margin: 5px 0 9px;
}

.spelling-module-copy > span {
  color: #5f7069;
  font-size: 15px;
  line-height: 1.5;
}

.spelling-module-arrow {
  align-items: center;
  background: rgba(255, 255, 255, .78);
  border-radius: 50%;
  display: flex;
  font-size: 24px;
  height: 48px;
  justify-content: center;
  width: 48px;
}

.conversation-chapter-home {
  align-self: center;
  display: grid;
  gap: 22px;
  width: 100%;
}

.conversation-chapter-header {
  align-items: center;
  background: linear-gradient(135deg, #faece3 0%, #f8f2dc 100%);
  border: 1px solid #e2d3bd;
  border-radius: 28px;
  display: flex;
  justify-content: space-between;
  padding: 32px 40px;
}

.conversation-chapter-header h1 {
  color: #174b39;
  font-size: clamp(32px, 4vw, 46px);
  line-height: 1.08;
  margin: 5px 0 8px;
}

.conversation-chapter-header p {
  color: #52675e;
  font-size: 16px;
  line-height: 1.5;
  margin: 0;
}

.conversation-chapter-count {
  background: rgba(255, 255, 255, .82);
  border: 1px solid #e2d3bd;
  border-radius: 999px;
  color: #55715f;
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 800;
  margin-left: 24px;
  padding: 12px 18px;
}

.conversation-chapter-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.conversation-chapter-card {
  border: 1px solid;
  border-radius: 24px;
  color: #24473b;
  display: grid;
  gap: 17px;
  grid-template-columns: 58px minmax(0, 1fr);
  min-height: 265px;
  padding: 26px;
  position: relative;
  text-align: left;
  transition: box-shadow .2s ease, transform .2s ease;
}

.conversation-chapter-card:hover {
  box-shadow: 0 15px 30px rgba(36, 71, 59, .13);
  transform: translateY(-4px);
}

.conversation-chapter-card--mint {
  background: #edf6e8;
  border-color: #c8ddbf;
}

.conversation-chapter-card--sky {
  background: #e8f3f4;
  border-color: #c4dfe0;
}

.conversation-chapter-card--sun {
  background: #fbf2d9;
  border-color: #ead8a8;
}

.conversation-chapter-number {
  align-items: center;
  background: rgba(255, 255, 255, .82);
  border-radius: 16px;
  display: flex;
  font-size: 18px;
  font-weight: 800;
  height: 58px;
  justify-content: center;
  grid-column: 1;
  grid-row: 1 / span 2;
  width: 58px;
}

.conversation-chapter-copy {
  display: flex;
  flex-direction: column;
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
}

.conversation-chapter-copy small {
  color: #6c7f65;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .05em;
  text-transform: uppercase;
}

.conversation-chapter-copy strong {
  color: #174b39;
  font-size: 29px;
  line-height: 1.15;
  margin: 9px 0 3px;
}

.conversation-chapter-copy b {
  color: #315c45;
  font-size: 17px;
}

.conversation-chapter-copy > span {
  color: #5f7069;
  font-size: 13px;
  line-height: 1.5;
  margin-top: 10px;
}

.conversation-chapter-meta {
  align-items: center;
  display: flex;
  gap: 5px;
  grid-column: 2;
  grid-row: 2;
  min-width: 0;
}

.conversation-chapter-meta b {
  color: #174b39;
  font-size: 17px;
}

.conversation-chapter-meta small {
  color: #6c7f65;
  font-size: 12px;
}

.conversation-chapter-meta i {
  font-size: 20px;
  font-style: normal;
  margin-left: auto;
}

.blending-group-page {
  align-self: start;
  display: grid;
  gap: 16px;
  margin-top: calc(var(--signed-content-top-gap) - 16px);
  width: 100%;
}

.blending-group-header {
  align-items: center;
  background: linear-gradient(135deg, #edf5e7 0%, #f8f2dc 100%);
  border: 1px solid #cbd9be;
  border-radius: 24px;
  display: flex;
  justify-content: space-between;
  padding: 22px 30px;
}

.blending-group-header h1 {
  color: #174b39;
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.08;
  margin: 3px 0 5px;
}

.blending-group-header p {
  color: #52675e;
  font-size: 14px;
  margin: 0;
}

.blending-group-count {
  background: rgba(255, 255, 255, .8);
  border: 1px solid #cbd9be;
  border-radius: 999px;
  color: #55715f;
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 800;
  padding: 10px 16px;
}

.blending-group-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.word-blending-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.word-blending-card {
  align-items: center;
  border: 1px solid;
  border-radius: 20px;
  color: #174b39;
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr) 28px;
  min-height: 128px;
  padding: 16px;
  text-align: left;
  transition: box-shadow .2s ease, transform .2s ease;
}

.word-blending-card:hover,
.word-blending-card.selected {
  box-shadow: 0 12px 25px rgba(36, 71, 59, .13);
  transform: translateY(-3px);
}

.word-blending-card.selected {
  outline: 3px solid #5f8d63;
  outline-offset: 2px;
}

.word-blending-main,
.word-blending-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.word-blending-main strong {
  font-size: 36px;
  line-height: 1.05;
}

.word-blending-main small,
.word-blending-details span {
  color: #607069;
  font-size: 12px;
}

.word-blending-details small {
  color: #6c7f65;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.word-blending-details strong {
  font-size: 17px;
  line-height: 1.25;
  margin: 3px 0;
}

.word-blending-details span {
  text-transform: capitalize;
}

.word-blending-arrow {
  align-items: center;
  background: rgba(255, 255, 255, .72);
  border-radius: 50%;
  display: flex;
  font-size: 16px;
  height: 28px;
  justify-content: center;
  width: 28px;
}

.blending-group-card {
  align-items: center;
  border: 1px solid;
  border-radius: 20px;
  color: #174b39;
  display: grid;
  gap: 10px;
  grid-template-columns: 58px minmax(0, 1fr) auto;
  min-height: 112px;
  padding: 14px;
  position: relative;
  text-align: left;
  transition: box-shadow .2s ease, transform .2s ease;
}

.blending-group-card:hover,
.blending-group-card.selected {
  box-shadow: 0 12px 25px rgba(36, 71, 59, .13);
  transform: translateY(-3px);
}

.blending-group-card.selected {
  outline: 3px solid #5f8d63;
  outline-offset: 2px;
}

.blending-group-card--mint {
  background: #edf6e8;
  border-color: #c8ddbf;
}

.blending-group-card--sun {
  background: #fbf2d9;
  border-color: #ead8a8;
}

.blending-group-card--sky {
  background: #e8f3f4;
  border-color: #c4dfe0;
}

.blending-group-card--peach {
  background: #faece3;
  border-color: #ebcebc;
}

.blending-group-vowel {
  align-items: center;
  background: rgba(255, 255, 255, .82);
  border-radius: 15px;
  display: flex;
  font-size: 34px;
  font-weight: 800;
  height: 58px;
  justify-content: center;
  width: 58px;
}

.blending-group-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.blending-group-copy small,
.blending-group-sign small {
  color: #6c7f65;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.blending-group-copy strong {
  font-size: 25px;
  line-height: 1.1;
  margin: 2px 0;
}

.blending-group-copy > span {
  color: #607069;
  font-size: 12px;
}

.blending-group-sign {
  align-items: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 68px;
  text-align: center;
}

.blending-group-sign strong {
  font-size: clamp(16px, 1.35vw, 20px);
  line-height: 1.15;
  white-space: nowrap;
}

.blending-group-arrow {
  bottom: 8px;
  color: #51705e;
  font-size: 15px;
  position: absolute;
  right: 11px;
}

.blending-selection-note {
  color: #60745f;
  font-size: 13px;
  margin: -2px 0 0;
  text-align: center;
}

@media (max-width: 950px) {
  .blending-group-grid,
  .word-blending-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.vowel-lesson-header {
  align-items: center;
  background: linear-gradient(135deg, #edf5e7 0%, #f8f2dc 100%);
  border: 1px solid #cbd9be;
  border-radius: 28px;
  display: flex;
  gap: 28px;
  justify-content: space-between;
  padding: 32px 40px;
}

.vowel-lesson-header h1 {
  color: #174b39;
  font-size: clamp(34px, 4vw, 46px);
  line-height: 1.08;
  margin: 0 0 10px;
}

.vowel-lesson-header p {
  color: #52675e;
  font-size: 16px;
  line-height: 1.55;
  margin: 0;
  max-width: 680px;
}

.vowel-progress {
  background: rgba(255, 255, 255, .82);
  border: 1px solid #cbd9be;
  border-radius: 18px;
  display: grid;
  flex: 0 0 180px;
  gap: 4px;
  padding: 16px 18px;
}

.vowel-progress > span:first-child {
  color: #72816a;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.vowel-progress strong {
  color: #174b39;
  font-size: 18px;
}

.vowel-progress-track {
  background: #dfe8d7;
  border-radius: 999px;
  display: block;
  height: 7px;
  margin-top: 5px;
  overflow: hidden;
}

.vowel-progress-track span {
  background: #5f8d63;
  border-radius: inherit;
  display: block;
  height: 100%;
  width: 9.09%;
}

.single-vowel-card {
  background: linear-gradient(150deg, #f3f6ed 0%, #f8f7ec 100%);
  border: 1px solid #d3ddca;
  border-radius: 28px;
  box-shadow: 0 18px 42px rgba(36, 71, 59, .09);
  min-width: 0;
  overflow: visible;
  padding: 30px;
  position: relative;
}

.single-vowel-topline {
  align-items: center;
  display: flex;
  justify-content: space-between;
}

.word-lesson-topline > span:last-child {
  color: #71806c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.word-lesson-main {
  align-items: center;
  display: grid;
  gap: 44px;
  grid-template-columns: minmax(230px, .9fr) minmax(300px, 1.1fr);
  min-height: 268px;
  padding: 14px 58px 24px;
}

.word-illustration-shell {
  align-items: center;
  aspect-ratio: 384 / 341;
  background: rgba(255, 255, 255, .82);
  border: 1px solid #d8e1d2;
  border-radius: 24px;
  display: flex;
  justify-content: center;
  justify-self: center;
  max-width: 280px;
  overflow: hidden;
  padding: 10px;
  width: 100%;
}

.word-illustration {
  height: 100%;
  object-fit: contain;
  width: 100%;
}

.word-lesson-copy {
  border-left: 1px solid #cbd8c4;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 10px 0 10px 48px;
}

.word-lesson-copy > span:first-child {
  color: #71806c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.word-lesson-copy h1 {
  color: #174b39;
  font-size: clamp(78px, 9vw, 118px);
  line-height: .95;
  margin: 8px 0 4px;
}

.word-ipa-row {
  align-items: center;
  display: flex;
  gap: 18px;
}

.word-ipa-row > strong {
  color: #174b39;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 38px;
  font-weight: 400;
}

.word-lesson-copy > small {
  color: #66776c;
  font-size: 14px;
  margin-top: 2px;
}

.word-lesson-copy > p {
  color: #315c45;
  font-size: 21px;
  font-weight: 800;
  margin: 8px 0 0;
  text-transform: capitalize;
}

.word-blend-tip {
  margin-top: 0;
  padding-right: 28px;
}

.word-blend-tip .pronunciation-tip-icon {
  flex-basis: 44px;
  font-family: inherit;
  font-size: 12px;
  height: 44px;
}

.word-blend-tip h2 {
  font-size: 25px;
  margin-bottom: 4px;
}

.number-lesson-topline > span:last-child {
  color: #71806c;
  font-size: 13px;
  font-weight: 800;
}

.number-lesson-main {
  align-items: center;
  display: grid;
  gap: 50px;
  grid-template-columns: minmax(260px, .9fr) minmax(320px, 1.1fr);
  min-height: 300px;
  padding: 18px 70px 28px;
}

.number-bengali-digit {
  color: #174b39;
  font-size: clamp(180px, 20vw, 270px);
  font-weight: 800;
  line-height: .85;
  text-align: center;
}

.number-lesson-copy {
  border-left: 1px solid #cbd8c4;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 24px 0 24px 54px;
}

.number-lesson-copy > span:first-child {
  color: #71806c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.number-lesson-copy h1 {
  color: #174b39;
  font-size: clamp(54px, 6vw, 82px);
  line-height: 1.05;
  margin: 12px 0 22px;
}

.number-ipa-row strong {
  color: #2c6248;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 42px;
  font-weight: 400;
  line-height: 1;
}

.number-lesson-copy > small {
  color: #5f7069;
  font-size: 14px;
  margin-top: 9px;
}

.number-lesson-copy > p {
  color: #315c45;
  font-size: 21px;
  font-weight: 800;
  margin: 8px 0 0;
}

.number-match-tip {
  margin-top: 0;
}

.number-match-tip .pronunciation-tip-icon {
  flex-basis: 54px;
  font-family: inherit;
  font-size: 12px;
  height: 54px;
}

.conversation-lesson-topline > span:last-child {
  color: #71806c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}

.story-reading-main {
  margin: 0 auto;
  max-width: 960px;
  min-height: 410px;
  padding: 28px 58px 38px;
  width: 100%;
}

.story-reading-main > .student-eyebrow {
  color: #71806c;
}

.story-reading-main > h1 {
  color: #174b39;
  font-size: clamp(34px, 4vw, 50px);
  line-height: 1.2;
  margin: 8px 0 26px;
}

.story-bangla-text {
  display: grid;
  gap: 18px;
}

.story-bangla-text p {
  color: #174b39;
  font-size: clamp(22px, 2.1vw, 30px);
  line-height: 1.65;
  margin: 0;
}

.story-translation {
  border-top: 1px solid #cbd8c4;
  margin-top: 30px;
  padding-top: 18px;
}

.story-translation summary {
  color: #315c45;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: .05em;
  text-transform: uppercase;
}

.story-translation > div {
  background: rgba(255, 255, 255, .76);
  border: 1px solid #d4ddcf;
  border-radius: 18px;
  display: grid;
  gap: 10px;
  margin-top: 14px;
  padding: 20px 24px;
}

.story-translation p {
  color: #50685b;
  font-size: 16px;
  line-height: 1.55;
  margin: 0;
}

.story-reading-main:focus-visible {
  border-radius: 18px;
  outline: 3px solid #174b39;
  outline-offset: -3px;
}

.conversation-lesson-main {
  min-height: 410px;
  margin: 0 auto;
  max-width: 940px;
  padding: 30px 58px 62px;
  position: relative;
  width: 100%;
}

.conversation-message-avatar {
  align-items: center;
  background: #dcebd7;
  border-radius: 50%;
  color: #174b39;
  display: flex;
  flex: 0 0 auto;
  font-weight: 800;
  justify-content: center;
}

.conversation-chat-area {
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.conversation-message-row {
  align-items: flex-end;
  display: flex;
  gap: 10px;
  max-width: 88%;
}

.conversation-message-row--sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.conversation-message-avatar {
  background: #fff;
  border: 1px solid #c9d8ce;
  font-size: 12px;
  height: 34px;
  width: 34px;
}

.conversation-message-row--sent .conversation-message-avatar {
  background: #d7ead2;
}

.conversation-flashcard {
  appearance: none;
  background: transparent;
  border: 0;
  min-height: 150px;
  min-width: min(560px, 70vw);
  padding: 0;
  perspective: 1200px;
  text-align: left;
}

.conversation-flashcard-inner {
  display: grid;
  height: 100%;
  min-height: 150px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform .45s cubic-bezier(.2, .75, .25, 1);
}

.conversation-flashcard.flipped .conversation-flashcard-inner {
  transform: rotateY(180deg);
}

.conversation-flashcard-face {
  backface-visibility: hidden;
  border: 1px solid #d2ddd5;
  border-radius: 8px 18px 18px 18px;
  box-shadow: 0 5px 13px rgba(42, 76, 60, .1);
  display: flex;
  flex-direction: column;
  grid-area: 1 / 1;
  justify-content: center;
  min-height: 150px;
  padding: 18px 22px;
  position: relative;
  width: 100%;
}

.conversation-flashcard-front {
  background: #fff;
}

.conversation-message-row--sent .conversation-flashcard-face {
  border-radius: 18px 8px 18px 18px;
}

.conversation-message-row--sent .conversation-flashcard-front {
  background: #dff1d8;
}

.conversation-flashcard-back {
  background: #fff8df;
  transform: rotateY(180deg);
}

.conversation-flashcard-front strong {
  color: #174b39;
  font-size: clamp(25px, 2.25vw, 34px);
  line-height: 1.28;
}

.conversation-card-hint {
  bottom: 20px;
  color: #789084;
  font-size: 12px;
  position: absolute;
  right: 58px;
}

.conversation-flashcard-back > strong {
  color: #174b39;
  font-size: 19px;
  line-height: 1.3;
}

.conversation-ipa {
  color: #315c45;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 18px;
  margin-top: 8px;
}

.conversation-flashcard-back small {
  color: #66776c;
  font-size: 12px;
  margin-top: 5px;
}

.conversation-flashcard:focus-visible {
  border-radius: 18px;
  outline: 3px solid #174b39;
  outline-offset: 4px;
}

.conversation-tip {
  margin-top: 0;
}

.conversation-tip .pronunciation-tip-icon {
  flex-basis: 52px;
  font-family: inherit;
  font-size: 12px;
  height: 52px;
}

.single-vowel-letter-wrap {
  align-items: center;
  display: grid;
  gap: 34px;
  grid-template-columns: minmax(220px, .8fr) 1.2fr;
  min-width: 0;
  min-height: 270px;
  padding: 16px 56px 28px;
}

.single-vowel-letter {
  color: #174b39;
  font-size: clamp(150px, 19vw, 230px);
  font-weight: 800;
  line-height: .9;
  text-align: center;
}

.vowel-sidebar-progress {
  background: linear-gradient(145deg, #edf5e7, #f8f7ec);
  border: 1px solid #d3ddca;
  border-radius: 22px;
  box-shadow: 0 14px 32px rgba(36, 71, 59, .09);
  color: #60745f;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 22px;
}

.vowel-lesson-stage {
  --lesson-side-space: 0px;
  align-self: center;
  display: grid;
  gap: 16px;
  justify-self: center;
  min-width: 0;
  padding-inline: var(--lesson-side-space);
  position: relative;
  padding-bottom: 58px;
  width: 100%;
}

.vowel-sidebar-progress > span:first-child {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.vowel-sidebar-progress > strong {
  color: #174b39;
  font-size: 30px;
  line-height: 1;
}

.vowel-sidebar-progress > small {
  color: #6c7f65;
  font-size: 13px;
  line-height: 1.4;
}

.vowel-study-progress-track {
  background: #dce6d5;
  border-radius: 999px;
  display: block;
  height: 7px;
  overflow: hidden;
  width: 100%;
}

.vowel-study-progress-track > span {
  background: #5f8d63;
  border-radius: inherit;
  display: block;
  height: 100%;
  transition: width .25s ease;
  width: 9.09%;
}

.consonant-progress-rail {
  align-items: center;
  background: transparent;
  border: 0;
  border-radius: 0;
  box-shadow: none;
  gap: 0;
  min-height: 0;
  padding: 0;
}

.consonant-progress-rail > span:first-child,
.consonant-progress-rail > strong {
  display: none;
}

.consonant-dot-track {
  display: grid;
  grid-template-columns: repeat(var(--lesson-steps), minmax(0, 1fr));
  grid-template-rows: 44px;
  height: 44px;
  margin: 0 auto;
  max-width: none;
  min-height: 44px;
  position: relative;
  width: 100%;
}

.consonant-dot-track::before {
  background: #d6ded8;
  border-radius: 999px;
  bottom: auto;
  content: '';
  height: 4px;
  left: 7px;
  position: absolute;
  right: 7px;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
}

.consonant-progress-dot {
  align-items: center;
  appearance: none;
  background: transparent;
  border: 0;
  cursor: pointer;
  display: flex;
  justify-content: center;
  min-height: 0;
  padding: 0;
  position: relative;
  width: 100%;
  z-index: 1;
}

.consonant-progress-dot::before {
  background: #fff;
  border: 2px solid #c8d3cc;
  border-radius: 50%;
  box-sizing: border-box;
  content: '';
  height: 14px;
  transition: background .18s ease, box-shadow .18s ease, transform .18s ease;
  width: 14px;
}

.consonant-progress-dot.completed::before {
  background: #5f8d63;
  border-color: #5f8d63;
}

.consonant-progress-dot.current::before {
  background: #174b39;
  border-color: #fff;
  box-shadow: 0 0 0 5px #cfe0d1, 0 0 0 7px #174b39;
  height: 19px;
  width: 19px;
}

.consonant-progress-dot:hover::before,
.consonant-progress-dot:focus-visible::before {
  background: #2c6248;
  transform: scale(1.45);
}

.consonant-progress-dot:focus-visible {
  outline: 2px solid #174b39;
  outline-offset: 1px;
}

.vowel-pagination {
  inset: 0;
  pointer-events: none;
  position: absolute;
}

.vowel-pagination > span {
  bottom: -48px;
  color: #6c7f65;
  font-size: 17px;
  font-weight: 800;
  left: 50%;
  position: absolute;
  transform: translateX(-50%);
  white-space: nowrap;
}

.vowel-pagination button {
  align-items: center;
  background: #2c6248;
  border: 2px solid #2c6248;
  border-radius: 50%;
  box-shadow: 0 7px 16px rgba(32, 63, 48, .16);
  color: #fff;
  display: flex;
  height: 54px;
  justify-content: center;
  min-height: 0;
  min-width: 0;
  padding: 0;
  pointer-events: auto;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 54px;
}

.vowel-pagination button:first-child {
  left: -82px;
}

.vowel-pagination button:last-child {
  right: -82px;
}

.vowel-pagination button:hover:not(:disabled) {
  background: #203f30;
  border-color: #203f30;
  transform: translateY(-50%) scale(1.08);
}

.vowel-pagination button:disabled {
  background: #b7c8bd;
  border-color: #b7c8bd;
  color: #fff;
}

.page-triangle {
  display: block;
  height: 0;
  width: 0;
}

.page-triangle--left {
  border-bottom: 8px solid transparent;
  border-right: 12px solid currentColor;
  border-top: 8px solid transparent;
  margin-left: -3px;
}

.page-triangle--right {
  border-bottom: 8px solid transparent;
  border-left: 12px solid currentColor;
  border-top: 8px solid transparent;
  margin-right: -3px;
}

@media (min-width: 1401px) {
  .student-lesson-content .vowel-sidebar-progress {
    position: absolute;
    right: calc(100% + 28px);
    top: 0;
    width: 210px;
  }
}

.student-lesson-content .vowel-lesson-stage {
  padding-bottom: 100px;
}

.student-lesson-content .vowel-sidebar-progress.consonant-progress-rail {
  bottom: 0;
  left: var(--lesson-side-space);
  position: absolute;
  right: var(--lesson-side-space);
  top: auto;
  width: auto;
}

@media (min-width: 601px) and (max-width: 1700px) {
  .student-lesson-content .vowel-lesson-stage {
    --lesson-side-space: 82px;
  }
}

.single-vowel-transcription {
  border-left: 1px solid #cbd8c4;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 20px 0 20px 48px;
}

.single-vowel-transcription span {
  color: #71806c;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.single-vowel-transcription strong {
  color: #174b39;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(52px, 8vw, 82px);
  font-weight: 400;
  line-height: 1.2;
  margin: 10px 0 2px;
}

.vowel-ipa-row {
  align-items: flex-end;
  display: flex;
  gap: 20px;
}

.single-vowel-transcription small {
  color: #66776c;
  font-size: 15px;
}

.consonant-inherent-note {
  color: #607069;
  font-size: 12px;
  line-height: 1.35;
  margin: 9px 0 0;
  max-width: 360px;
}

.consonant-inherent-note b {
  color: #4f6f59;
  font-weight: 800;
}

.consonant-vowel-picker {
  align-items: center;
  background: rgba(255, 255, 255, .78);
  border: 1px solid #d8e1d2;
  border-radius: 16px;
  display: flex;
  gap: 16px;
  margin: -4px 0 14px;
  padding: 10px 14px;
}

.consonant-vowel-picker > span {
  color: #66815b;
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .06em;
  text-transform: uppercase;
}

.consonant-vowel-picker > div {
  display: grid;
  flex: 1;
  gap: 7px;
  grid-template-columns: repeat(11, minmax(34px, 1fr));
  min-width: 0;
}

.consonant-vowel-picker button {
  align-items: center;
  background: #f4f7ef;
  border: 1px solid #cbd8c7;
  border-radius: 10px;
  color: #315c45;
  display: flex;
  height: 36px;
  justify-content: center;
  min-height: 0;
  min-width: 0;
  padding: 0;
}

.consonant-vowel-picker button span {
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
}

.consonant-vowel-picker button:hover,
.consonant-vowel-picker button.selected {
  background: #2c6248;
  border-color: #2c6248;
  color: #fff;
}

.pronunciation-tip {
  align-items: flex-start;
  background: #fff;
  border: 1px solid #d8e1d2;
  border-radius: 20px;
  display: flex;
  gap: 16px;
  margin-bottom: 0;
  min-width: 0;
  padding: 22px 86px 22px 22px;
}

.pronunciation-tip > div {
  min-width: 0;
}

.pronunciation-tip-icon {
  align-items: center;
  background: #dfeeda;
  border-radius: 50%;
  color: #2c6248;
  display: flex;
  flex: 0 0 34px;
  font-family: Georgia, serif;
  font-size: 20px;
  font-weight: 700;
  height: 34px;
  justify-content: center;
}

.pronunciation-tip h2 {
  color: #174b39;
  font-size: 22px;
  margin: 1px 0 8px;
}

.pronunciation-tip p {
  color: #56675f;
  line-height: 1.6;
  margin: 0;
}

.vowel-example {
  align-items: center;
  background: #e8f3f4;
  border: 1px solid #c4dfe0;
  border-radius: 20px;
  display: flex;
  gap: 26px;
  justify-content: space-between;
  margin-right: 68px;
  padding: 18px 22px;
}

.vowel-example > div {
  display: flex;
  flex-direction: column;
}

.vowel-example strong {
  color: #174b39;
  font-size: 34px;
  line-height: 1.2;
}

.vowel-example > div:last-child {
  align-items: flex-end;
}

.vowel-example > div:last-child span {
  color: #174b39;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 20px;
}

.vowel-example small {
  color: #687a72;
  font-size: 13px;
}

.vowel-speaker-button {
  align-items: center;
  background: #2c513e;
  border: 1px solid #2c513e;
  border-radius: 50%;
  box-shadow: 0 8px 18px rgba(32, 63, 48, .22);
  color: #fff;
  display: flex;
  flex: 0 0 52px;
  height: 52px;
  justify-content: center;
  padding: 0;
  width: 52px;
}

.vowel-speaker-button:hover {
  background: #203f30;
  transform: translateY(-2px);
}

.vowel-speaker-button svg {
  height: 25px;
  width: 25px;
}

.vowel-feedback {
  background: #e9f2e4;
  border: 1px solid #c7d9bd;
  border-radius: 14px;
  color: #2c513e;
  margin: -12px 0 0;
  padding: 13px 16px;
}

.vowel-completion-celebration {
  align-items: center;
  animation: celebration-backdrop 2.4s ease both;
  background: rgba(244, 249, 240, .58);
  display: flex;
  inset: 0;
  justify-content: center;
  pointer-events: none;
  position: fixed;
  z-index: 100;
}

.vowel-completion-message {
  align-items: center;
  animation: celebration-message 2.4s cubic-bezier(.2, .8, .2, 1) both;
  background: #fff;
  border: 1px solid #c7d9bd;
  border-radius: 26px;
  box-shadow: 0 24px 60px rgba(23, 75, 57, .22);
  color: #174b39;
  display: flex;
  flex-direction: column;
  max-width: min(350px, calc(100vw - 40px));
  padding: 24px 30px;
  position: relative;
  text-align: center;
  z-index: 2;
}

.vowel-completion-message > span {
  align-items: center;
  background: #2c6248;
  border-radius: 50%;
  color: #fff;
  display: flex;
  font-size: 23px;
  font-weight: 800;
  height: 46px;
  justify-content: center;
  margin-bottom: 11px;
  width: 46px;
}

.vowel-completion-message strong {
  font-size: 24px;
  line-height: 1.15;
}

.vowel-completion-message p {
  color: #5f7069;
  font-size: 14px;
  margin: 7px 0 0;
}

.firework {
  height: 12px;
  position: absolute;
  width: 12px;
}

.firework--one {
  left: 28%;
  top: 28%;
}

.firework--two {
  animation-delay: .22s;
  right: 27%;
  top: 25%;
}

.firework--three {
  animation-delay: .42s;
  bottom: 24%;
  left: 52%;
}

.firework span {
  --spark-angle: calc(var(--spark) * 30deg);
  animation: firework-spark 1.35s ease-out both;
  animation-delay: inherit;
  background: #4f8a59;
  border-radius: 999px;
  height: 22px;
  left: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%) rotate(var(--spark-angle)) translateY(-12px) scaleY(.15);
  transform-origin: center;
  width: 5px;
}

.firework span:nth-child(3n + 2) {
  background: #e0ad3d;
}

.firework span:nth-child(3n) {
  background: #e88061;
}

@keyframes celebration-backdrop {
  0%, 100% { opacity: 0; }
  8%, 84% { opacity: 1; }
}

@keyframes celebration-message {
  0% { opacity: 0; transform: translateY(18px) scale(.88); }
  12% { opacity: 1; transform: translateY(0) scale(1.04); }
  18%, 84% { opacity: 1; transform: translateY(0) scale(1); }
  100% { opacity: 0; transform: translateY(-8px) scale(.98); }
}

@keyframes firework-spark {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) rotate(var(--spark-angle)) translateY(-12px) scaleY(.15);
  }
  18% { opacity: 1; }
  72% {
    opacity: 1;
    transform: translate(-50%, -50%) rotate(var(--spark-angle)) translateY(-72px) scaleY(1);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) rotate(var(--spark-angle)) translateY(-86px) scaleY(.35);
  }
}

@media (prefers-reduced-motion: reduce) {
  .vowel-completion-celebration,
  .vowel-completion-message,
  .firework span {
    animation-duration: .01ms;
  }
}

.profile-card-actions {
  display: flex;
  gap: 8px;
}

.profile-edit-button,
.profile-delete-button {
  background: transparent;
  border: 0;
  font-size: 15px;
  font-weight: 700;
  min-height: 40px;
  padding: 8px 16px;
}

.profile-edit-button {
  color: #2c6248;
}

.profile-delete-button {
  color: #914832;
}

.profile-edit-button:hover,
.profile-delete-button:hover {
  text-decoration: underline;
}

.profile-delete-confirm {
  background: #faf0e9;
  border-radius: 12px;
  color: #713b2c;
  padding: 14px;
  width: 100%;
}

.profile-delete-confirm p {
  font-size: 14px;
  margin: 0 0 12px;
}

.profile-delete-confirm label {
  font-size: 14px;
  margin: 0 0 7px;
  text-align: left;
}

.profile-delete-confirm input {
  font-size: 15px;
  min-height: 48px;
  padding: 11px 14px;
}

.profile-delete-confirm .field-error {
  margin: 7px 0 0;
  text-align: left;
}

.profile-delete-confirm > div {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.profile-delete-confirm .danger,
.profile-delete-confirm .secondary {
  margin: 0;
  min-height: 44px;
  padding: 10px 12px;
}

.sr-only {
  clip: rect(0, 0, 0, 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}

.password-field input {
  padding-right: 50px;
}

@media (min-width: 601px) {
  .account-content.student-content:not(.student-lesson-content) {
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
    height: auto;
    max-width: none;
    min-height: calc(100svh - 36px);
  }

  .student-content:not(.student-lesson-content) .student-home {
    grid-template-rows: auto minmax(0, 1fr);
    min-height: 0;
  }

  .student-content:not(.student-lesson-content) .student-home-content {
    align-self: center;
    gap: clamp(12px, 1.8vh, 20px);
    transform: translateY(clamp(4px, 1vh, 12px));
  }

  .student-content:not(.student-lesson-content) .student-footer {
    margin-top: 0;
  }

  .account-content.student-lesson-content {
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
    min-height: calc(100svh - 36px);
  }

  .student-lesson-content .student-home {
    grid-template-rows: auto minmax(0, 1fr);
    min-height: 0;
  }

  .student-lesson-content .vowel-lesson-stage {
    align-self: start;
    margin-top: calc(var(--signed-content-top-gap) - 16px);
  }

  .student-lesson-content .student-footer {
    margin-top: 0;
  }

  .account-session {
    margin-bottom: var(--signed-content-top-gap);
    min-height: 64px;
    padding-block: 8px;
  }

  .account-content.profiles-content {
    max-width: var(--signed-page-width);
  }

  .account-content.profiles-content > h1 {
    font-size: 36px;
    margin-bottom: 8px;
  }

  .account-content.profiles-content > .subtitle {
    font-size: 16px;
    margin-bottom: 20px;
  }

  .family-meta {
    margin-bottom: 14px;
  }

  .profile-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }

  .profile-card,
  .add-profile {
    min-height: 0;
    padding: 14px 12px;
  }

  .profile-card {
    gap: 5px;
  }

  .profile-avatar-image {
    height: 72px;
    width: 72px;
  }

  .profile-learn-button {
    margin-top: 4px;
    min-height: 38px;
    padding-block: 7px;
  }

  .profile-card-actions button {
    min-height: 34px;
    padding-block: 5px;
  }

  .child-empty-state {
    margin-top: 22px;
    padding: 28px;
  }

  .child-empty-icon {
    height: 58px;
    margin-bottom: 10px;
  }

  .child-empty-state p {
    font-size: 17px;
    margin-bottom: 18px;
  }

  .child-profile-form .avatar-fieldset {
    margin-top: 14px;
  }

  .profile-avatar-options {
    gap: 9px;
  }

  .child-form-actions {
    margin-top: 18px;
  }

  .account-page.student-page {
    padding-bottom: 18px;
    padding-top: 18px;
  }

  .student-nav {
    margin-top: -18px;
    min-height: 64px;
    padding-block: 8px;
  }

  .student-brand-mark {
    border-radius: 11px;
    font-size: 22px;
    height: 44px;
    width: 44px;
  }

  .student-nav-avatar {
    flex-basis: 36px;
    height: 36px;
    width: 36px;
  }

  .student-home {
    gap: 16px;
  }

  .student-welcome {
    border-radius: 22px;
    min-height: clamp(205px, 25svh, 286px);
    padding: clamp(18px, 2.3vh, 26px) 34px;
    transform: none;
  }

  .student-welcome-animation-space {
    min-height: clamp(42px, 7.5svh, 92px);
  }

  .student-welcome h1 {
    font-size: 38px;
    margin-bottom: 6px;
  }

  .student-welcome p {
    font-size: 16px;
  }

  .student-level-pill {
    min-width: 170px;
    padding: 14px 18px;
  }

  .learning-area-heading h2 {
    font-size: 27px;
  }

  .learning-area-grid {
    gap: 16px;
  }

  .learning-area-card {
    border-radius: 20px;
    gap: 16px;
    min-height: clamp(108px, 13svh, 148px);
    padding: clamp(14px, 1.8vh, 20px) 22px;
  }

  .learning-area-symbol {
    border-radius: 18px;
    font-size: clamp(21px, 2vw, 24px);
    height: clamp(62px, 7vh, 78px);
    width: clamp(96px, 9vw, 112px);
  }

  .learning-area-copy strong {
    font-size: 22px;
    margin: 2px 0 3px;
  }

  .learning-area-copy > span {
    font-size: 14px;
    line-height: 1.35;
  }

  .student-footer {
    margin-top: 18px;
  }

  .single-vowel-card {
    border-radius: 22px;
    padding: 22px 28px;
  }

  .single-vowel-letter-wrap {
    min-height: 225px;
    padding: 8px 56px 18px;
  }

  .single-vowel-letter {
    font-size: clamp(130px, 17vh, 185px);
  }

  .pronunciation-tip {
    padding: 18px 22px;
  }

  .pronunciation-tip h2 {
    font-size: 20px;
    margin-bottom: 4px;
  }

  .pronunciation-tip p {
    font-size: 14px;
    line-height: 1.45;
  }
}

@media (min-width: 601px) and (max-width: 900px) {
  .student-nav {
    gap: 14px;
    padding-inline: 16px;
  }

  .student-brand {
    gap: 8px;
    min-width: 0;
  }

  .student-brand > span:last-child {
    min-width: 0;
  }

  .student-brand strong,
  .student-brand small {
    white-space: nowrap;
  }

  .student-nav-account {
    flex: 0 0 auto;
  }

  .student-content:not(.student-lesson-content) .student-home-content {
    align-self: start;
    padding-top: 22px;
    transform: none;
  }

  .student-welcome {
    gap: 16px;
    min-height: 280px;
    padding: 24px 28px;
    transform: none;
  }

  .student-welcome h1 {
    font-size: clamp(32px, 4.5vw, 38px);
  }

  .student-welcome-animation-space {
    min-height: 48px;
  }

  .learning-area-grid {
    gap: 14px;
  }

  .learning-area-card {
    gap: 14px;
    grid-template-columns: 92px minmax(0, 1fr) 40px;
    min-height: 150px;
    padding: 18px;
  }

  .learning-area-symbol {
    height: 76px;
    width: 92px;
  }

  .learning-area-copy strong {
    font-size: 20px;
  }

  .learning-area-copy > span {
    font-size: 13px;
  }

  .learning-area-arrow {
    align-self: center;
    height: 40px;
    width: 40px;
  }

  .spelling-module-header {
    padding: 26px 28px;
  }

  .spelling-module-grid {
    gap: 16px;
  }

  .spelling-module-card {
    align-content: start;
    gap: 14px;
    grid-template-columns: 96px minmax(0, 1fr);
    min-height: 220px;
    padding: 22px;
  }

  .spelling-module-symbol {
    border-radius: 19px;
    font-size: 27px;
    height: 82px;
    width: 96px;
  }

  .spelling-module-copy strong {
    font-size: 23px;
  }

  .spelling-module-arrow {
    display: none;
  }

  .conversation-chapter-header {
    padding: 26px 28px;
  }

  .conversation-chapter-grid {
    grid-template-columns: 1fr;
  }

  .conversation-chapter-card {
    min-height: 165px;
  }

  .student-lesson-content .vowel-lesson-stage {
    --lesson-side-space: 58px;
  }

  .single-vowel-card {
    padding: 20px;
  }

  .single-vowel-letter-wrap {
    gap: 18px;
    grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
    min-height: 220px;
    padding: 8px 24px 18px;
  }

  .single-vowel-letter {
    font-size: clamp(108px, 18vw, 158px);
  }

  .single-vowel-letter.special-sign-display {
    font-size: clamp(88px, 14vw, 130px);
  }

  .word-lesson-main {
    gap: 24px;
    grid-template-columns: minmax(190px, .85fr) minmax(250px, 1.15fr);
    min-height: 230px;
    padding: 12px 24px 18px;
  }

  .word-illustration-shell {
    max-width: 230px;
  }

  .word-lesson-copy {
    padding-left: 28px;
  }

  .word-lesson-copy h1 {
    font-size: clamp(66px, 10vw, 92px);
  }

  .word-ipa-row > strong {
    font-size: 32px;
  }

  .number-lesson-main {
    gap: 28px;
    grid-template-columns: minmax(190px, .85fr) minmax(250px, 1.15fr);
    min-height: 250px;
    padding: 14px 30px 22px;
  }

  .number-bengali-digit {
    font-size: clamp(150px, 24vw, 205px);
  }

  .number-lesson-copy {
    padding: 18px 0 18px 32px;
  }

  .number-lesson-copy h1 {
    font-size: clamp(46px, 7vw, 64px);
  }

  .conversation-lesson-main {
    min-height: 390px;
    padding: 14px 20px 52px;
  }

  .story-reading-main {
    min-height: 390px;
    padding: 18px 28px 30px;
  }

  .conversation-card-hint {
    bottom: 16px;
    right: 20px;
  }

  .conversation-flashcard {
    min-width: min(500px, 66vw);
  }

  .conversation-flashcard-front strong {
    font-size: clamp(23px, 3.2vw, 30px);
  }

  .single-vowel-transcription {
    padding: 14px 0 14px 26px;
  }

  .single-vowel-transcription strong {
    font-size: clamp(44px, 7vw, 66px);
  }

  .vowel-ipa-row {
    gap: 14px;
  }

  .vowel-speaker-button {
    flex-basis: 52px;
    height: 52px;
    width: 52px;
  }

  .pronunciation-tip {
    gap: 12px;
    padding: 17px 18px;
  }

  .pronunciation-tip h2 {
    font-size: 19px;
  }

  .pronunciation-tip p {
    overflow-wrap: anywhere;
  }

  .consonant-vowel-picker {
    align-items: flex-start;
  }

  .consonant-vowel-picker > div {
    grid-template-columns: repeat(6, minmax(34px, 1fr));
  }

  .vowel-pagination button {
    height: 48px;
    width: 48px;
  }

  .vowel-pagination button:first-child {
    left: -58px;
  }

  .vowel-pagination button:last-child {
    right: -58px;
  }
}

@media (max-width: 600px) {
  .account-session {
    align-items: center;
    gap: 10px;
    margin-bottom: 38px;
    min-height: 72px;
    padding: 10px 16px;
  }

  .account-session .text-button {
    padding: 7px 8px;
  }

  .account-session-pin,
  .account-session-user {
    gap: 7px;
  }

  .account-session-user {
    min-width: 0;
  }

  .account-session-user strong {
    max-width: 145px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .account-session-user .text-button {
    padding-left: 12px;
  }

  .pin-status {
    display: none;
  }

  .child-empty-state {
    margin-top: 30px;
    padding: 38px 20px;
  }

  .profile-avatar-options {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .child-form-actions {
    grid-template-columns: 1fr;
  }

  .account-page.student-page {
    padding-top: 0;
  }

  .student-nav {
    gap: 10px;
    margin-top: 0;
    min-height: 72px;
    padding: 10px 16px;
  }

  .student-nav-account {
    gap: 8px;
  }

  .student-signout {
    min-height: 40px;
    padding: 7px 8px 7px 12px;
  }

  .student-brand-mark {
    border-radius: 11px;
    font-size: 22px;
    height: 44px;
    width: 44px;
  }

  .student-nav-account small {
    display: none;
  }

  .student-brand small {
    display: block;
    font-size: 12px;
    line-height: 1.15;
    margin-top: 2px;
    white-space: nowrap;
  }

  .student-brand strong {
    font-size: 14px;
    line-height: 1.15;
  }

  .student-nav-account > div {
    min-width: 0;
  }

  .student-nav-account strong {
    max-width: 84px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .student-welcome {
    align-items: flex-start;
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    min-height: 300px;
    padding: 28px 24px;
  }

  .student-welcome-animation-space {
    grid-column: 1;
    min-height: 56px;
  }

  .student-level-pill {
    width: 100%;
  }

  .learning-area-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .learning-area-grid {
    grid-template-columns: 1fr;
  }

  .spelling-module-home {
    align-self: start;
    gap: 16px;
    padding-top: 24px;
  }

  .spelling-module-header {
    align-items: flex-start;
    border-radius: 22px;
    flex-direction: column;
    gap: 15px;
    padding: 24px;
  }

  .spelling-module-header h1 {
    font-size: 30px;
  }

  .spelling-module-header p {
    font-size: 14px;
  }

  .spelling-module-count {
    margin-left: 0;
  }

  .spelling-module-grid {
    grid-template-columns: 1fr;
  }

  .spelling-module-card {
    gap: 16px;
    grid-template-columns: 92px minmax(0, 1fr);
    min-height: 0;
    padding: 20px;
  }

  .spelling-module-symbol {
    border-radius: 18px;
    font-size: 25px;
    height: 76px;
    width: 92px;
  }

  .spelling-module-copy strong {
    font-size: 22px;
    margin-bottom: 5px;
  }

  .spelling-module-copy > span {
    font-size: 13px;
  }

  .spelling-module-arrow {
    display: none;
  }

  .conversation-chapter-home {
    align-self: start;
    gap: 16px;
    padding-top: 24px;
  }

  .conversation-chapter-header {
    align-items: flex-start;
    border-radius: 22px;
    flex-direction: column;
    gap: 15px;
    padding: 24px;
  }

  .conversation-chapter-header h1 {
    font-size: 30px;
  }

  .conversation-chapter-header p {
    font-size: 14px;
  }

  .conversation-chapter-count {
    margin-left: 0;
  }

  .conversation-chapter-grid {
    grid-template-columns: 1fr;
  }

  .conversation-chapter-card {
    min-height: 230px;
    padding: 20px;
  }

  .conversation-chapter-copy strong {
    font-size: 25px;
  }

  .conversation-chapter-meta {
    bottom: 17px;
    left: 95px;
    right: 20px;
  }

  .blending-group-page {
    margin-top: 24px;
  }

  .blending-group-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
    padding: 22px;
  }

  .blending-group-grid {
    grid-template-columns: 1fr;
  }

  .word-blending-grid {
    grid-template-columns: 1fr;
  }

  .learning-area-card {
    grid-template-columns: auto 1fr;
    min-height: 0;
    padding: 20px;
  }

  .learning-area-symbol {
    border-radius: 18px;
    font-size: 21px;
    height: 70px;
    width: 104px;
  }

  .learning-area-arrow {
    display: none;
  }

  .vowel-progress {
    flex-basis: auto;
    width: 100%;
  }

  .student-lesson-content .vowel-lesson-stage {
    --lesson-side-space: 58px;
  }

  .consonant-progress-rail {
    min-height: 0;
    width: 100%;
  }

  .consonant-dot-track {
    grid-template-columns: repeat(var(--lesson-steps), minmax(0, 1fr));
    grid-template-rows: 28px;
    height: 28px;
    min-height: 28px;
    width: 100%;
  }

  .consonant-dot-track::before {
    bottom: auto;
    height: 2px;
    left: 4px;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    width: auto;
  }

  .consonant-progress-dot {
    height: 28px;
    width: 100%;
  }

  .single-vowel-card {
    padding: 22px;
  }

  .word-lesson-topline {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .word-lesson-main {
    gap: 16px;
    grid-template-columns: 1fr;
    min-height: 0;
    padding: 22px 0 18px;
  }

  .word-illustration-shell {
    margin-inline: auto;
    max-width: 250px;
    width: 100%;
  }

  .word-lesson-copy {
    align-items: center;
    border-left: 0;
    border-top: 1px solid #cbd8c4;
    padding: 18px 0 0;
    text-align: center;
  }

  .word-lesson-copy h1 {
    font-size: clamp(68px, 22vw, 96px);
  }

  .word-blend-tip {
    padding: 18px;
  }

  .number-lesson-topline {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .number-lesson-main {
    gap: 16px;
    grid-template-columns: 1fr;
    min-height: 0;
    padding: 24px 0 18px;
  }

  .number-bengali-digit {
    font-size: clamp(150px, 48vw, 210px);
  }

  .number-lesson-copy {
    align-items: center;
    border-left: 0;
    border-top: 1px solid #cbd8c4;
    padding: 22px 0 0;
    text-align: center;
  }

  .number-lesson-copy h1 {
    font-size: clamp(46px, 15vw, 68px);
    margin-bottom: 16px;
  }

  .number-ipa-row strong {
    font-size: 36px;
  }

  .number-match-tip {
    padding: 18px;
  }

  .conversation-lesson-topline {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .conversation-lesson-main {
    min-height: 0;
    padding: 20px 0 18px;
  }

  .story-reading-main {
    min-height: 0;
    padding: 24px 4px 20px;
  }

  .story-reading-main > h1 {
    font-size: clamp(30px, 9vw, 40px);
    margin-bottom: 20px;
  }

  .story-bangla-text {
    gap: 15px;
  }

  .story-bangla-text p {
    font-size: clamp(20px, 6vw, 26px);
  }

  .story-translation > div {
    padding: 16px;
  }

  .conversation-chat-area {
    gap: 12px;
    min-height: 300px;
    padding: 16px 12px 48px;
  }

  .conversation-card-hint {
    bottom: 12px;
    right: 14px;
  }

  .conversation-message-row {
    gap: 7px;
    max-width: 100%;
    width: 100%;
  }

  .conversation-message-avatar {
    height: 30px;
    width: 30px;
  }

  .conversation-flashcard {
    flex: 1;
    min-height: 150px;
    min-width: 0;
    width: calc(100% - 37px);
  }

  .conversation-flashcard-inner,
  .conversation-flashcard-face {
    min-height: 150px;
  }

  .conversation-flashcard-face {
    padding: 15px;
  }

  .conversation-flashcard-front strong {
    font-size: clamp(22px, 6.5vw, 28px);
    overflow-wrap: anywhere;
  }

  .conversation-flashcard-back > strong {
    font-size: 17px;
  }

  .conversation-ipa {
    font-size: 15px;
    overflow-wrap: anywhere;
  }

  .conversation-tip {
    padding: 18px;
  }

  .single-vowel-letter-wrap {
    gap: 10px;
    grid-template-columns: 1fr;
    min-height: 0;
    padding: 32px 0;
  }

  .single-vowel-letter {
    font-size: 150px;
  }

  .single-vowel-transcription {
    align-items: center;
    border-left: 0;
    border-top: 1px solid #cbd8c4;
    padding: 24px 0 0;
    text-align: center;
  }

  .consonant-vowel-picker {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }

  .consonant-vowel-picker > div {
    grid-template-columns: repeat(6, minmax(34px, 1fr));
  }

  .pronunciation-tip {
    padding: 20px;
  }

  .vowel-pagination > span {
    text-align: center;
  }

  .vowel-pagination button {
    height: 46px;
    width: 46px;
  }

  .vowel-pagination button:first-child {
    left: -58px;
  }

  .vowel-pagination button:last-child {
    right: -58px;
  }
}

.single-vowel-letter.special-sign-display {
  font-size: clamp(105px, 13vw, 170px);
  letter-spacing: -.06em;
}

@media (max-width: 700px) {
  .quiz-launcher-grid {
    grid-template-columns: 1fr;
  }

  .quiz-launcher-card,
  .quiz-header,
  .quiz-submit-row,
  .quiz-result-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .quiz-page {
    margin-top: 22px;
    padding-inline: 16px;
  }

  .quiz-progress-pill {
    width: 100%;
  }

  .quiz-options {
    margin-left: 0;
  }

  .quiz-feedback {
    grid-template-columns: 36px minmax(0, 1fr);
  }

  .quiz-feedback > strong {
    grid-column: 2;
  }

  .quiz-history li {
    grid-template-columns: 1fr auto;
  }

  .quiz-history li small {
    grid-column: 1 / -1;
    text-align: left;
  }
}

</style>
