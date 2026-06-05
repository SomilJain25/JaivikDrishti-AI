import { useLanguage } from '../context/LanguageContext'
import { ExternalLink } from 'lucide-react'
import pmKisanIcon from '../assets/PM_KISAN_circular.png'
import pmfby1Icon from '../assets/PMFBY_1_circular.png'
import sinchaiIcon from '../assets/PM_Krishi_Sinchai_circular.png'
import kcc1Icon from '../assets/KCC_1_circular.png'
import soilIcon from '../assets/Soil_Health_Card_circular.png'
import vistaarIcon from '../assets/Bharat_VISTAAR_circular.png'
const schemes = [
  {
    id: 1,
    title: 'Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)',
    titleHi: 'प्रधानमंत्री किसान सम्मान निधि (पीएम-किसान)',
    desc: '₹6,000 yearly support in 3 installments and Direct bank transfer to farmers',
    descHi: 'किसान परिवारों को ₹6,000/वर्ष की आय सहायता',
    icon: pmKisanIcon,
    color: 'bg-orange-500',
    link: 'https://pmkisan.gov.in/'
  },
  {
    id: 2,
    title: 'Pradhan Mantri Fasal Bima Yojana (PMFBY)',
    titleHi: 'प्रधानमंत्री फसल बीमा योजना (PMFBY)',
    desc: 'Crop insurance against flood, drought, pests, etc.',
    descHi: 'बाढ़, सूखा, कीटों आदि से फसल का बीमा।',
    icon: pmfby1Icon,
    color: 'bg-purple-600',
    link: 'https://pmfby.gov.in/'
  },
  {
    id: 3,
    title: 'PM Krishi Sinchai Yojana',
    titleHi: 'प्रधानमंत्री कृषि सिंचाई योजना (पीएमकेएसवाई)',
    desc: 'Irrigation and water management support for farmers',
    descHi: 'किसानों के लिए सिंचाई और जल प्रबंधन समर्थन',
    icon: sinchaiIcon,
    color: 'bg-purple-600',
    link: 'https://pmksy.mowr.gov.in/'
  },
 
  {
    id: 4,
    title: 'Kisan Credit Card',
    titleHi: 'किसान क्रेडिट कार्ड',
    desc: 'Easy credit access at low interest rates',
    descHi: 'कम ब्याज दर पर आसान ऋण पहुंच',
    icon: kcc1Icon,
    color: 'bg-blue-600',
    link: 'https://www.pib.gov.in/indexd.aspx?reg=3&lang=2'
  },
   {
    id: 5,
    title: 'Soil Health Card',
    titleHi: 'स्वस्थ मिट्टी कार्ड',
    desc: 'Free soil testing and health report for better farming',
    descHi: 'बेहतर खेती के लिए मुफ्त मिट्टी परीक्षण',
    icon: soilIcon,
    color: 'bg-green-600',
    link: 'https://soilhealth.dac.gov.in/home'
  },
  {
    id: 6,
    title: 'Bharat-VISTAAR',
    titleHi: 'बहरत-विस्तार',
    desc: 'New multilingual AI agriculture advisory platform announced in Budget 2024',
    descHi: 'बजट 2024 में घोषित नई बहुभाषी एआई कृषि सलाहकार प्लेटफॉर्म',
    icon: vistaarIcon,
    color: 'bg-green-600',
    link: 'https://vistaar.da.gov.in/'
  }
]

export default function GovtSchemes() {
  const { lang, t } = useLanguage()
  
  return (
    <section className="py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-bold gradient-text mb-2">
            {t.govSchemes}
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            {lang === 'en' 
              ? 'Explore government initiatives designed to support and empower farmers across India'
              : 'भारत भर में किसानों का समर्थन और सशक्तिकरण करने के लिए डिज़ाइन की गई सरकारी पहलों का अन्वेषण करें'
            }
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {schemes.map((scheme, idx) => {
            return (
              <a
                key={scheme.id}
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className="
                  group
                  min-w-[280px]
                  sm:min-w-[320px]
                  lg:min-w-[340px]
                  flex-shrink-0
                  snap-start
                  bg-white rounded-2xl p-5 shadow-md
                  hover:shadow-xl transition-all
                  duration-300 border border-gray-100
                  hover:-translate-y-1
                "
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className="flex gap-4 items-start">

                  {/* Left Icon */}
                  <div
                    className={`w-14 h-14 ${scheme.color} rounded-2xl flex items-center justify-center
                    group-hover:scale-110 transition-transform flex-shrink-0 overflow-hidden`}
                  >
                    <img
                      src={scheme.icon}
                      alt={scheme.title}
                      className="w-9 h-9 object-contain"
                    />
                  </div>

                  {/* Right Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-gray-800 group-hover:text-primary-700 transition-colors mb-2">
                      {lang === 'en'
                        ? scheme.title
                        : scheme.titleHi}
                    </h3>

                    <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                      {lang === 'en'
                        ? scheme.desc
                        : scheme.descHi}
                    </p>

                    <div className="flex items-center text-sm font-medium text-primary-700">
                      <span>{t.viewDetails}</span>

                      <ExternalLink className="w-4 h-4 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>

                </div>
              </a>
            )
          })}
        </div>
      </div>
    </section>
  )
}