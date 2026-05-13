import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function ModuleCard({ 
  title, 
  description, 
  icon: Icon, 
  to, 
  colorClass, 
  bgGradient,
  delay = 0 
}) {
  return (
    <Link
      to={to}
      className="group block"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={`relative overflow-hidden rounded-2xl p-6 h-full 
                      bg-white border border-gray-100 shadow-lg card-hover
                      animate-slide-up`}>
        {/* Gradient background on hover */}
        <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 ${bgGradient}`} />
        
        {/* Icon */}
        <div className={`w-14 h-14 rounded-2xl ${colorClass} flex items-center justify-center 
                        mb-4 group-hover:scale-110 transition-transform duration-300 shadow-md`}>
          <Icon className="w-7 h-7 text-white" />
        </div>
        
        {/* Content */}
        <h3 className="text-xl font-bold text-gray-800 mb-2 group-hover:text-primary-700 transition-colors">
          {title}
        </h3>
        <p className="text-gray-600 text-sm leading-relaxed mb-4">
          {description}
        </p>
        
        {/* CTA */}
        <div className="flex items-center text-sm font-semibold text-primary-700 group-hover:gap-2 transition-all">
          <span>Explore</span>
          <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all -ml-1 group-hover:ml-0" />
        </div>
        
        {/* Decorative corner */}
        <div className={`absolute -bottom-4 -right-4 w-24 h-24 rounded-full ${colorClass} opacity-5 
                        group-hover:scale-150 transition-transform duration-500`} />
      </div>
    </Link>
  )
}